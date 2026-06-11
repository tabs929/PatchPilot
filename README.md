# PatchPilot

An autonomous [SWE-bench](https://www.swebench.com/) agent. This repo currently
implements **Phase 0** (a working grading harness) and **Phase 1** (a dumb
end-to-end oracle-retrieval baseline using Anthropic Claude).

A SWE-bench task is a repo at a fixed commit plus a GitHub issue. Your output is
a git diff, graded by hidden tests inside Docker: `FAIL_TO_PASS` (the bug is
fixed) and `PASS_TO_PASS` (nothing else breaks).

## Layout

```
src/patchpilot/
  config.py        paths, dataset selection, model ids, cost table
  dataset.py       load SWE-bench Lite, select slices
  repos.py         clone + checkout repos at base_commit
  oracle.py        derive gold-touched files (Phase 1 "cheat")
  model_client.py  Anthropic wrapper: retries + token/cost tracking
  prompts.py       oracle editing prompt
  edit.py          full-file rewrites -> git diff (the model_patch)
  predictions.py   read/write swebench JSONL predictions
  pipeline.py      solve one instance end to end
scripts/
  validate_gold.sh Phase 0: run gold patch(es) through the harness
  run_eval.sh      run the harness over a predictions file
  score.py         parse harness output -> resolution rate + table
  run_baseline.py  Phase 1: oracle baseline over a slice
```

## Prerequisites (one-time)

1. **Docker Desktop** (the harness grades inside containers). In Docker settings
   allocate ~120GB virtual disk and >=16GB RAM. Verify with `docker run hello-world`.
   On Apple Silicon, image support is "experimental"; we pass `--namespace ''` so
   images build locally instead of pulling x86-only DockerHub images. First builds
   are slow.
2. **uv** (already installed here). If `uv` is not on your PATH:
   `source $HOME/.local/bin/env`.
3. **API key**: `cp .env.example .env` and set `ANTHROPIC_API_KEY`.

## Setup

```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e .
python -m swebench.harness.run_evaluation --help   # sanity check
```

## Phase 0 - validate the harness on a gold patch

```bash
scripts/validate_gold.sh validate-gold sympy__sympy-20590
python scripts/score.py --run-id validate-gold --model gold
```

A correctly set-up harness reports the gold instance as `RESOLVED`.

## Phase 1 - dumb oracle baseline

```bash
# Generate predictions for a small slice (oracle retrieval).
python scripts/run_baseline.py --limit 5

# Grade + score (or pass --run-eval to do it in one step).
scripts/run_eval.sh predictions/baseline.jsonl oracle-baseline-v0 4
python scripts/score.py --run-id oracle-baseline-v0
```

`run_baseline.py` checks out each repo at `base_commit`, gives Claude the issue
plus the gold-touched files, asks for full rewritten files, diffs them into a
patch, and writes `predictions/baseline.jsonl`.

## Model strategy

Iterate with a cheap, fast model on a tiny slice; only run larger slices with
your best model. Configure slugs in `.env` (`PATCHPILOT_ITERATION_MODEL`,
`PATCHPILOT_FINAL_MODEL`) or per-run with `--model`. Confirm the exact Anthropic
slugs against the current model list before a real run.

## Correctness / no leakage

The oracle uses only the gold patch's **file list** - never its contents and
never the hidden `test_patch` / `FAIL_TO_PASS` tests. The model sees only the
issue and the current file contents.

## Roadmap (later phases)

2. Real localization (remove the oracle) + localization recall metric.
3. Agent loop + multi-file editing with search/replace blocks.
4. Verification & self-correction against legitimately reproducible tests.
5. Scale, cost tracking, failure-mode breakdown.
6. Observability (trajectory logs), writeup, optional PR-opening surface.
