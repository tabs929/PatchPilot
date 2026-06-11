"""Clone repos and check them out at an instance's base_commit.

One clone is cached per repo under repos_cache/. Because Phase 0-1 process
instances sequentially, we reuse the single clone and reset it to a pristine
state before each checkout.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from . import config


def repo_dir(repo: str) -> Path:
    return config.REPOS_CACHE / repo.replace("/", "__")


def _run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)


def ensure_repo(repo: str) -> Path:
    """Clone https://github.com/<repo>.git into the cache if not present."""
    d = repo_dir(repo)
    if not (d / ".git").exists():
        d.parent.mkdir(parents=True, exist_ok=True)
        _run(["git", "clone", f"https://github.com/{repo}.git", str(d)])
    return d


def checkout(repo: str, commit: str) -> Path:
    """Reset the cached clone to a pristine checkout of `commit`. Returns the path."""
    d = ensure_repo(repo)
    # Discard any edits from a previous instance, then move to the target commit.
    _run(["git", "reset", "--hard"], cwd=d, check=False)
    _run(["git", "clean", "-fd"], cwd=d, check=False)
    res = _run(["git", "checkout", "-f", commit], cwd=d, check=False)
    if res.returncode != 0:
        # Commit may not be present locally (shallow/old); fetch everything and retry.
        _run(["git", "fetch", "--all", "--tags"], cwd=d)
        _run(["git", "checkout", "-f", commit], cwd=d)
    _run(["git", "clean", "-fd"], cwd=d, check=False)
    return d


def read_file(repo_path: Path, rel_path: str) -> str | None:
    p = repo_path / rel_path
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8", errors="replace")
