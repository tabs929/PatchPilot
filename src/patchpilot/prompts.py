"""Prompt construction for the Phase 1 oracle editing step.

The model receives the issue text and the FULL contents of the oracle-selected
files. It must return the complete rewritten contents of any file it changes,
wrapped in <file path="..."> ... </file> markers. We then diff those rewrites
against the checkout to produce a clean, reliably-appliable patch.
"""

from __future__ import annotations

SYSTEM = """You are an expert software engineer fixing a bug in a real codebase.
You are given a GitHub issue and the full contents of the file(s) most likely to
need changes. Produce a minimal, correct fix.

Rules:
- Only change what is necessary to resolve the issue. Do not refactor unrelated code.
- Preserve the existing code style, indentation, and imports.
- For every file you modify, output its ENTIRE new contents (not a diff, not a
  snippet, no elisions or "..." placeholders).
- Wrap each modified file exactly like this, with nothing else around it:

<file path="RELATIVE/PATH/AS/GIVEN.py">
<the complete new file contents here>
</file>

- Do not wrap file contents in Markdown code fences.
- If a file does not need changes, do not output it.
- You may include a short explanation before the <file> blocks, but the blocks
  must contain only raw file contents."""


def build_oracle_prompt(problem_statement: str, file_contents: dict[str, str | None]) -> tuple[str, str]:
    parts: list[str] = []
    parts.append("# GitHub issue\n")
    parts.append(problem_statement.strip())
    parts.append("\n\n# Candidate files (full contents)\n")
    for path, content in file_contents.items():
        if content is None:
            parts.append(f"\n## {path}\n(FILE NOT FOUND IN CHECKOUT)\n")
            continue
        parts.append(f"\n## {path}\n")
        parts.append("```\n")
        parts.append(content)
        if not content.endswith("\n"):
            parts.append("\n")
        parts.append("```\n")
    parts.append(
        "\n# Task\nFix the issue. Output the complete new contents of every file you "
        "change using the <file path=\"...\"> ... </file> format described above."
    )
    return SYSTEM, "".join(parts)
