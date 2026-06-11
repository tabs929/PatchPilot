"""Central configuration: paths, dataset selection, model ids, cost table.

Everything here is overridable via environment variables (loaded from .env)
so the same code runs with a cheap model on a tiny slice during iteration and
a frontier model on the final run.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Repo root is two levels up from this file (src/patchpilot/config.py).
ROOT = Path(__file__).resolve().parents[2]
REPOS_CACHE = Path(os.environ.get("PATCHPILOT_REPOS_CACHE", ROOT / "repos_cache"))
PREDICTIONS_DIR = Path(os.environ.get("PATCHPILOT_PREDICTIONS_DIR", ROOT / "predictions"))
LOGS_DIR = Path(os.environ.get("PATCHPILOT_LOGS_DIR", ROOT / "logs"))

# Dataset. SWE-bench Lite has splits: test (300) and dev (23).
DATASET_NAME = os.environ.get("PATCHPILOT_DATASET", "princeton-nlp/SWE-bench_Lite")
DATASET_SPLIT = os.environ.get("PATCHPILOT_SPLIT", "test")

# Anthropic model slugs. These are sensible defaults but you MUST confirm them
# against the current Anthropic model list before a real run.
ITERATION_MODEL = os.environ.get("PATCHPILOT_ITERATION_MODEL", "claude-haiku-4-5")
FINAL_MODEL = os.environ.get("PATCHPILOT_FINAL_MODEL", "claude-sonnet-4-5")
DEFAULT_MODEL = os.environ.get("PATCHPILOT_MODEL", ITERATION_MODEL)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Written into predictions as model_name_or_path and used to locate harness logs
# under logs/run_evaluation/<run_id>/<MODEL_NAME_OR_PATH>/.
MODEL_NAME_OR_PATH = os.environ.get("PATCHPILOT_MODEL_NAME", "patchpilot-oracle")

# Apple Silicon: empty string makes the harness build images locally instead of
# pulling x86-only images from DockerHub.
NAMESPACE = os.environ.get("PATCHPILOT_NAMESPACE", "")

MAX_OUTPUT_TOKENS = int(os.environ.get("PATCHPILOT_MAX_TOKENS", "16384"))

# USD per 1M tokens, as (input, output). Used only for rough cost reporting;
# update to match current Anthropic pricing. Unknown models fall back to DEFAULT_PRICE.
DEFAULT_PRICE = (1.0, 5.0)
MODEL_PRICES = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-3-5-haiku-latest": (0.80, 4.0),
    "claude-3-5-sonnet-latest": (3.0, 15.0),
}


def price_for(model: str) -> tuple[float, float]:
    return MODEL_PRICES.get(model, DEFAULT_PRICE)


def ensure_dirs() -> None:
    for d in (REPOS_CACHE, PREDICTIONS_DIR, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)
