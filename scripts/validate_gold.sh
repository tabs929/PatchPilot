#!/usr/bin/env bash
# Phase 0: run gold patch(es) through the harness to confirm the loop reports
# "resolved". On Apple Silicon, --namespace '' builds images locally.
#
# Usage:
#   scripts/validate_gold.sh [run_id] [instance_id ...]
# Examples:
#   scripts/validate_gold.sh                       # default single instance
#   scripts/validate_gold.sh validate-gold sympy__sympy-20590 astropy__astropy-12907
set -euo pipefail

RUN_ID="${1:-validate-gold}"
shift || true
if [ "$#" -gt 0 ]; then
  INSTANCES=("$@")
else
  INSTANCES=("sympy__sympy-20590")
fi

DATASET="${PATCHPILOT_DATASET:-princeton-nlp/SWE-bench_Lite}"
MAX_WORKERS="${PATCHPILOT_MAX_WORKERS:-1}"

python -m swebench.harness.run_evaluation \
  --dataset_name "$DATASET" \
  --predictions_path gold \
  --instance_ids "${INSTANCES[@]}" \
  --run_id "$RUN_ID" \
  --namespace '' \
  --max_workers "$MAX_WORKERS"

echo
echo "Now score it:"
echo "  python scripts/score.py --run-id $RUN_ID --model gold"
