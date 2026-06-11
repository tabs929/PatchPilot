"""Oracle retrieval: derive the set of files the gold patch edits.

This is the Phase 1 "cheat" that isolates the editing problem from the
retrieval problem. We parse only the gold diff's file list, NOT its contents or
the hidden test patch, so the model never sees the solution or grading tests.
"""

from __future__ import annotations

from typing import Any

from unidiff import PatchSet


def gold_files(instance: dict[str, Any]) -> list[str]:
    """Return repo-relative paths modified by the instance's gold patch."""
    patch_text = instance.get("patch") or ""
    if not patch_text.strip():
        return []
    patch = PatchSet(patch_text)
    files: list[str] = []
    for f in patch:
        # Prefer the post-image path; fall back to the pre-image for deletions.
        path = f.path if f.path and f.path != "/dev/null" else f.source_file
        path = _strip_prefix(path)
        if path and path not in files:
            files.append(path)
    return files


def _strip_prefix(path: str) -> str:
    if path.startswith(("a/", "b/")):
        return path[2:]
    return path
