#!/usr/bin/env python3
"""Phase 1: dumb end-to-end oracle baseline over a small slice of instances.

For each instance: check out base_commit, hand the model the gold-touched files
(oracle), ask for full-file rewrites, diff them into a model_patch, and write a
swebench predictions JSONL. Optionally invoke the grading harness and score it.

Examples:
  python scripts/run_baseline.py --limit 5
  python scripts/run_baseline.py --instance-ids sympy__sympy-20590 --run-eval
  python scripts/run_baseline.py --split dev --limit 10 --model claude-haiku-4-5
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from patchpilot import config, dataset, predictions  # noqa: E402
from patchpilot.model_client import ModelClient  # noqa: E402
from patchpilot.pipeline import solve_instance  # noqa: E402

console = Console()


def main() -> int:
    ap = argparse.ArgumentParser(description="PatchPilot oracle baseline (Phase 1).")
    ap.add_argument("--instance-ids", nargs="*", default=None)
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--split", default=None, help="dataset split (default from config: test)")
    ap.add_argument("--dataset", default=None)
    ap.add_argument("--model", default=None, help="Anthropic model slug (default from config)")
    ap.add_argument("--out", default=str(config.PREDICTIONS_DIR / "baseline.jsonl"))
    ap.add_argument("--run-eval", action="store_true", help="invoke the grading harness afterwards")
    ap.add_argument("--run-id", default="oracle-baseline-v0")
    ap.add_argument("--max-workers", type=int, default=4)
    args = ap.parse_args()

    config.ensure_dirs()

    instances = dataset.select_instances(
        instance_ids=args.instance_ids,
        limit=None if args.instance_ids else args.limit,
        dataset_name=args.dataset,
        split=args.split,
    )
    console.print(f"Loaded [bold]{len(instances)}[/bold] instance(s).")

    client = ModelClient(model=args.model)
    console.print(f"Using model [bold]{client.model}[/bold].")

    results = []
    table = Table(title="Oracle baseline results")
    table.add_column("instance_id", overflow="fold")
    table.add_column("oracle files", justify="right")
    table.add_column("changed", justify="right")
    table.add_column("patch bytes", justify="right")
    table.add_column("status")

    for i, instance in enumerate(instances, 1):
        console.print(f"[dim]({i}/{len(instances)})[/dim] solving {instance['instance_id']} ...")
        res = solve_instance(instance, client)
        results.append(res)
        status = "[red]ERROR[/red]" if res.error else (
            "[yellow]empty patch[/yellow]" if not res.model_patch.strip() else "[green]patched[/green]"
        )
        table.add_row(
            res.instance_id,
            str(len(res.oracle_files)),
            str(len(res.changed_files)),
            str(len(res.model_patch.encode("utf-8"))),
            status + (f" {res.error}" if res.error else ""),
        )

    out_path = predictions.write_predictions(
        args.out, [r.to_prediction() for r in results]
    )

    console.print(table)
    console.print(f"\nWrote predictions -> [bold]{out_path}[/bold]")
    console.print(f"[dim]{client.usage_summary()}[/dim]")

    if args.run_eval:
        console.print("\nRunning grading harness ...")
        cmd = [
            "python", "-m", "swebench.harness.run_evaluation",
            "--dataset_name", args.dataset or config.DATASET_NAME,
            "--predictions_path", str(out_path),
            "--run_id", args.run_id,
            "--namespace", config.NAMESPACE,
            "--max_workers", str(args.max_workers),
        ]
        subprocess.run(cmd, check=False)
        console.print(f"\nScore it with:\n  python scripts/score.py --run-id {args.run_id}")
    else:
        console.print(
            "\nNext: grade and score:\n"
            f"  scripts/run_eval.sh {out_path} {args.run_id} {args.max_workers}\n"
            f"  python scripts/score.py --run-id {args.run_id}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
