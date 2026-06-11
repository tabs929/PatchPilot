"""Orchestrate solving a single instance with oracle retrieval.

instance -> checkout base_commit -> oracle file list -> prompt Claude ->
parse full-file rewrites -> git diff -> prediction dict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import config, edit, oracle, prompts, repos
from .model_client import ModelClient


@dataclass
class SolveResult:
    instance_id: str
    model_patch: str
    oracle_files: list[str]
    changed_files: list[str]
    raw_response: str
    error: str | None = None

    def to_prediction(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "model_name_or_path": config.MODEL_NAME_OR_PATH,
            "model_patch": self.model_patch,
        }


def solve_instance(instance: dict[str, Any], client: ModelClient) -> SolveResult:
    instance_id = instance["instance_id"]
    try:
        repo_path = repos.checkout(instance["repo"], instance["base_commit"])
        files = oracle.gold_files(instance)
        file_contents = {f: repos.read_file(repo_path, f) for f in files}

        system, user = prompts.build_oracle_prompt(instance["problem_statement"], file_contents)
        response = client.complete(system, user)

        rewrites = edit.parse_files(response)
        # Guard against the model touching files outside the oracle set.
        rewrites = {p: c for p, c in rewrites.items() if p in set(files)} or rewrites
        patch = edit.apply_and_diff(repo_path, rewrites)

        return SolveResult(
            instance_id=instance_id,
            model_patch=patch,
            oracle_files=files,
            changed_files=list(rewrites.keys()),
            raw_response=response,
        )
    except Exception as exc:  # noqa: BLE001 - surface per-instance failures, keep the batch going
        return SolveResult(
            instance_id=instance_id,
            model_patch="",
            oracle_files=[],
            changed_files=[],
            raw_response="",
            error=f"{type(exc).__name__}: {exc}",
        )
