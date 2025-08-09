#!/usr/bin/env python3
import json
import os
from typing import Dict, List

from datasets import load_dataset


def pick_split(ds_dict) -> str:
    """Pick a reasonable split to preview, preferring test, then validation, then train."""
    for cand in ("test", "validation", "train"):
        if cand in ds_dict:
            return cand
    # If datasets library returned a single Dataset instead of DatasetDict
    return None


def sample_dataset(name: str = "AfterQuery/FinanceQA", limit: int = 5) -> Dict[str, List[Dict]]:
    ds = load_dataset(name)
    split = pick_split(ds) if hasattr(ds, "keys") else None

    if split is None:
        # Single split dataset
        dset = ds
        split_name = "default"
    else:
        dset = ds[split]
        split_name = split

    n = min(limit, len(dset))
    subset = dset.select(range(n)) if n > 0 else dset

    records = []
    for ex in subset:
        # Keep only the most relevant fields to reduce local storage
        rec = {
            k: ex.get(k)
            for k in [
                "question",
                "answer",
                "context",
                "context_link",
                "question_type",
                "id",
            ]
            if k in ex
        }
        records.append(rec)

    return {"split": split_name, "count": len(records), "records": records}


def save_jsonl(path: str, records: List[Dict]):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    os.makedirs("temp", exist_ok=True)
    preview = sample_dataset()

    # Save JSONL for easy downstream processing
    out_path = os.path.join("temp", "financeqa_samples.jsonl")
    save_jsonl(out_path, preview["records"])

    # Also print a concise summary to stdout
    by_type: Dict[str, int] = {}
    for r in preview["records"]:
        t = (r.get("question_type") or "unknown").lower()
        by_type[t] = by_type.get(t, 0) + 1

    print(json.dumps({
        "split": preview["split"],
        "count": preview["count"],
        "by_question_type": by_type,
        "saved_to": out_path,
    }, indent=2))


if __name__ == "__main__":
    main()
