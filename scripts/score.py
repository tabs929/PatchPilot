#!/usr/bin/env python3
"""Parse swebench harness output into a resolution rate + per-instance table.

The harness writes per-instance reports at:
  logs/run_evaluation/<run_id>/<model_name_or_path>/<instance_id>/report.json
and a run summary at:
  <model_name_or_path>.<run_id>.json   (in the cwd it was launched from)

Usage:
  python scripts/score.py --run-id validate-gold
  python scripts/score.py --run-id oracle-baseline-v0 --model patchpilot-oracle
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make src/patchpilot importable without requiring an install.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

console = Console()


def find_reports(logs_dir: Path, run_id: str, model: str | None) -> list[Path]:
    base = logs_dir / run_id
    if model:
        base = base / model
    if not base.exists():
        return []
    return sorted(base.glob("**/report.json"))


def load_report(path: Path) -> dict:
    data = json.loads(path.read_text())
    # report.json is {instance_id: {...}}; flatten to the inner record.
    if len(data) == 1:
        (instance_id, record), = data.items()
        record = dict(record)
        record.setdefault("instance_id", instance_id)
        return record
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description="Score swebench harness output.")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--model", default=None, help="model_name_or_path (e.g. gold, patchpilot-oracle)")
    ap.add_argument("--logs-dir", default=str(ROOT / "logs" / "run_evaluation"))
    args = ap.parse_args()

    logs_dir = Path(args.logs_dir)
    reports = find_reports(logs_dir, args.run_id, args.model)

    if not reports:
        console.print(
            f"[red]No report.json found under {logs_dir / args.run_id}"
            + (f"/{args.model}" if args.model else "")
            + ".[/red]"
        )
        console.print("Did the harness finish? Check logs/run_evaluation/ and the build logs.")
        return 1

    table = Table(title=f"Resolution report - run_id={args.run_id}")
    table.add_column("instance_id", overflow="fold")
    table.add_column("applied")
    table.add_column("resolved")
    table.add_column("F2P pass/total", justify="right")
    table.add_column("P2P pass/total", justify="right")

    resolved = 0
    for path in reports:
        rec = load_report(path)
        instance_id = rec.get("instance_id", path.parent.name)
        applied = bool(rec.get("patch_successfully_applied", False))
        is_resolved = bool(rec.get("resolved", False))
        resolved += int(is_resolved)
        ts = rec.get("tests_status", {})
        f2p = ts.get("FAIL_TO_PASS", {})
        p2p = ts.get("PASS_TO_PASS", {})
        f2p_pass = len(f2p.get("success", []))
        f2p_total = f2p_pass + len(f2p.get("failure", []))
        p2p_pass = len(p2p.get("success", []))
        p2p_total = p2p_pass + len(p2p.get("failure", []))
        table.add_row(
            instance_id,
            "[green]yes[/green]" if applied else "[red]no[/red]",
            "[green]RESOLVED[/green]" if is_resolved else "[red]no[/red]",
            f"{f2p_pass}/{f2p_total}",
            f"{p2p_pass}/{p2p_total}",
        )

    console.print(table)
    total = len(reports)
    rate = resolved / total * 100 if total else 0.0
    console.print(
        f"\n[bold]Resolved {resolved}/{total} = {rate:.1f}%[/bold]  (run_id={args.run_id})"
    )

    # Show the harness summary file if present (lists empty/error instances too).
    for summary in ROOT.glob(f"*.{args.run_id}.json"):
        try:
            data = json.loads(summary.read_text())
        except json.JSONDecodeError:
            continue
        console.print(f"\n[dim]Harness summary {summary.name}:[/dim]")
        for k in (
            "total_instances",
            "submitted_instances",
            "completed_instances",
            "resolved_instances",
            "unresolved_instances",
            "empty_patch_instances",
            "error_instances",
        ):
            if k in data:
                console.print(f"  {k}: {data[k]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
