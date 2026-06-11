"""Load SWE-bench instances and select slices for iteration.

An instance is a dict with at least:
  - instance_id: "owner__repo-number"
  - repo: "owner/repo"
  - base_commit: commit to check out before editing
  - problem_statement: the GitHub issue text (model input)
  - patch: the gold diff (NEVER shown to the model; used only by the oracle
    to learn which files to edit, and by the harness for grading)
  - test_patch / FAIL_TO_PASS / PASS_TO_PASS: hidden grading info (never shown)
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from datasets import load_dataset

from . import config


def load_instances(dataset_name: Optional[str] = None, split: Optional[str] = None) -> list[dict[str, Any]]:
    dataset_name = dataset_name or config.DATASET_NAME
    split = split or config.DATASET_SPLIT
    ds = load_dataset(dataset_name, split=split)
    return [dict(row) for row in ds]


def select_instances(
    instance_ids: Optional[Iterable[str]] = None,
    limit: Optional[int] = None,
    dataset_name: Optional[str] = None,
    split: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Return instances filtered by id and/or truncated to `limit`."""
    rows = load_instances(dataset_name, split)
    if instance_ids:
        wanted = list(instance_ids)
        by_id = {r["instance_id"]: r for r in rows}
        missing = [i for i in wanted if i not in by_id]
        if missing:
            raise KeyError(f"instance_ids not found in {dataset_name}/{split}: {missing}")
        rows = [by_id[i] for i in wanted]
    if limit is not None:
        rows = rows[:limit]
    return rows


def get_instance(
    instance_id: str,
    dataset_name: Optional[str] = None,
    split: Optional[str] = None,
) -> dict[str, Any]:
    return select_instances([instance_id], dataset_name=dataset_name, split=split)[0]
