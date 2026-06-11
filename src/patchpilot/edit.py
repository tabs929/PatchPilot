"""Turn the model's full-file rewrites into a git diff (the model_patch).

Phase 1 strategy: the model returns whole files inside <file path="..."> blocks.
We write each file back into the checkout and let `git diff` produce the patch.
This applies 100% of the time, isolating reasoning quality from diff-application
brittleness. (Search/replace blocks arrive in Phase 3.)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_FILE_RE = re.compile(
    r'<file\s+path="(?P<path>[^"]+)"\s*>\n?(?P<body>.*?)\n?</file>',
    re.DOTALL,
)
_FENCE_RE = re.compile(r"^```[^\n]*\n(?P<inner>.*)\n```\s*$", re.DOTALL)


def parse_files(text: str) -> dict[str, str]:
    """Extract {relative_path: new_contents} from the model output."""
    out: dict[str, str] = {}
    for m in _FILE_RE.finditer(text):
        path = m.group("path").strip()
        body = m.group("body")
        fence = _FENCE_RE.match(body.strip())
        if fence:  # defensively unwrap accidental code fences
            body = fence.group("inner")
        if not body.endswith("\n"):
            body += "\n"
        out[path] = body
    return out


def apply_and_diff(repo_path: str | Path, files: dict[str, str]) -> str:
    """Write rewritten files into the checkout and return `git diff` output."""
    repo_path = Path(repo_path)
    for rel_path, content in files.items():
        target = repo_path / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    res = subprocess.run(
        ["git", "diff"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout
