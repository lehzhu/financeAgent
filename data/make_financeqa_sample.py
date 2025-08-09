#!/usr/bin/env python3
"""
Create a representative local sample of 50 items from AfterQuery/FinanceQA
and save to data/financeqa_50.jsonl.

Sampling strategy:
- Stratify by question_type to preserve distribution, with a minimum per type.
- If counts are small for some type, fill remaining quota from others.
"""
import json
import os
from collections import defaultdict
from typing import Dict, List

from datasets import load_dataset

import argparse

TARGET_SIZE_DEFAULT = 50
MIN_PER_TYPE_DEFAULT = 10  # try to keep at least 10 of each if available
DATASET_NAME = "AfterQuery/FinanceQA"


def save_jsonl(path: str, records: List[Dict]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=TARGET_SIZE_DEFAULT, help="target sample size (default 50)")
    parser.add_argument("--min-per-type", type=int, default=MIN_PER_TYPE_DEFAULT, help="minimum per question_type if available")
    parser.add_argument("--out", default=None, help="output JSONL path (default data/financeqa_<size>.jsonl)")
    args = parser.parse_args()

    target_size = args.size
    min_per_type = args.min_per_type

    out_path = args.out or os.path.join("data", f"financeqa_{target_size}.jsonl")

    ds = load_dataset(DATASET_NAME)
    split = "test" if "test" in ds else next(iter(ds.keys()))
    dset = ds[split]

    # Partition indices by question_type
    buckets: Dict[str, List[int]] = defaultdict(list)
    for i, ex in enumerate(dset):
        qtype = (ex.get("question_type") or "unknown").lower()
        buckets[qtype].append(i)

    # First pass: take up to min_per_type from each bucket
    chosen_idx: List[int] = []
    for qtype, idxs in buckets.items():
        take = min(min_per_type, len(idxs))
        chosen_idx.extend(idxs[:take])

    # Second pass: fill remaining up to target_size round-robin over buckets
    if len(chosen_idx) < target_size:
        remaining = target_size - len(chosen_idx)
        # Build an iterator across residual slices
        residuals = {k: buckets[k][min_per_type:] for k in buckets}
        # Flatten in round-robin order for fairness
        order = sorted(residuals.keys())
        ptrs = {k: 0 for k in order}
        while remaining > 0 and order:
            progressed = False
            for k in list(order):
                r = residuals[k]
                p = ptrs[k]
                if p < len(r):
                    chosen_idx.append(r[p])
                    ptrs[k] += 1
                    remaining -= 1
                    progressed = True
                    if remaining == 0:
                        break
                else:
                    # Exhausted this bucket
                    order.remove(k)
            if not progressed:
                break

    # If still not enough (dataset smaller than target), just cap
    chosen_idx = chosen_idx[: min(target_size, len(dset))]

    subset = dset.select(chosen_idx)

    # Keep key fields
    records: List[Dict] = []
    for ex in subset:
        rec = {k: ex.get(k) for k in (
            "id",
            "question",
            "answer",
            "context",
            "context_link",
            "question_type",
        ) if k in ex}
        records.append(rec)

    save_jsonl(out_path, records)

    # Print brief summary
    by_type: Dict[str, int] = defaultdict(int)
    for r in records:
        by_type[(r.get("question_type") or "unknown").lower()] += 1

    print(json.dumps({
        "split": split,
        "saved": len(records),
        "by_question_type": by_type,
        "path": out_path,
    }, indent=2))


if __name__ == "__main__":
    main()
