#!/usr/bin/env bash
# Run the swebench harness over a predictions JSONL file.
# On Apple Silicon, --namespace '' builds images locally.
#
# Usage:
#   scripts/run_eval.sh <predictions.jsonl> [run_id] [max_workers]
set -euo pipefail

PRED="${1:?usage: run_eval.sh <predictions.jsonl> [run_id] [max_workers]}"
RUN_ID="${2:-oracle-baseline-v0}"
MAX_WORKERS="${3:-${PATCHPILOT_MAX_WORKERS:-4}}"
DATASET="${PATCHPILOT_DATASET:-princeton-nlp/SWE-bench_Lite}"

python -m swebench.harness.run_evaluation \
  --dataset_name "$DATASET" \
  --predictions_path "$PRED" \
  --run_id "$RUN_ID" \
  --namespace '' \
  --max_workers "$MAX_WORKERS"

echo
echo "Now score it:"
echo "  python scripts/score.py --run-id $RUN_ID"
