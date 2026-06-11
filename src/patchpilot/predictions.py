"""Read/write predictions in the swebench JSONL format.

Each line is a JSON object with exactly the fields the harness expects:
  {"instance_id": ..., "model_name_or_path": ..., "model_patch": ...}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def write_predictions(path: str | Path, predictions: Iterable[dict[str, Any]]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for pred in predictions:
            f.write(json.dumps(_normalize(pred)) + "\n")
    return path


def _normalize(pred: dict[str, Any]) -> dict[str, Any]:
    return {
        "instance_id": pred["instance_id"],
        "model_name_or_path": pred["model_name_or_path"],
        "model_patch": pred.get("model_patch") or "",
    }


def read_predictions(path: str | Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
