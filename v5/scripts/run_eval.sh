#!/usr/bin/env bash
set -euo pipefail

DATASET=${1:-data/financeqa.json}
LIMIT=${2:-0}
OUT=${3:-eval/results.json}

python3 eval/evaluate.py --dataset "$DATASET" --limit "$LIMIT" --out "$OUT"

python3 - <<'PY'
import json
from eval.grading import grade

with open("eval/results.json") as f:
    res = json.load(f)

try:
    report = grade(res, "data/financeqa.json")
    print("Overall accuracy:", report["accuracy"]) 
    print("Calc accuracy:", report["calc_accuracy"]) 
except Exception as e:
    print("Skipping grading against gold due to:", e)
PY

