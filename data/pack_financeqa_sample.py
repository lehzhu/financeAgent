#!/usr/bin/env python3
"""
Pack data/financeqa_50.jsonl into a compact format:
- data/financeqa_50_index.csv (id, question_type, question, answer, context_path, context_link)
- data/contexts/<id>.txt containing the (potentially large) context text

This keeps the index small and loads large context lazily only when needed.
"""
import csv
import json
import os
from typing import Dict, List

import argparse

DEFAULT_INPUT_JSONL = os.path.join("data", "financeqa_50.jsonl")
DEFAULT_INDEX_CSV = os.path.join("data", "financeqa_50_index.csv")
DEFAULT_CONTEXTS_DIR = os.path.join("data", "contexts")


def read_jsonl(path: str) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT_JSONL, help="path to input JSONL")
    parser.add_argument("--index_csv", default=DEFAULT_INDEX_CSV, help="path to output index CSV")
    parser.add_argument("--contexts_dir", default=DEFAULT_CONTEXTS_DIR, help="directory to write context txt files")
    args = parser.parse_args()

    os.makedirs(args.contexts_dir, exist_ok=True)
    rows = read_jsonl(args.input)

    with open(args.index_csv, "w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["id", "question_type", "question", "answer", "context_path", "context_link"])  # header

        for ex in rows:
            ex_id = ex.get("id")
            # Fallback id if missing
            if ex_id is None:
                ex_id = f"row_{len(os.listdir(args.contexts_dir))}"
            ctx = ex.get("context") or ""
            ctx_filename = f"{ex_id}.txt"
            ctx_path = os.path.join(args.contexts_dir, ctx_filename)

            with open(ctx_path, "w", encoding="utf-8") as cf:
                cf.write(ctx)

            writer.writerow([
                ex_id,
                (ex.get("question_type") or "").lower(),
                ex.get("question") or "",
                ex.get("answer") or "",
                ctx_path,
                ex.get("context_link") or "",
            ])

    print(f"Wrote index: {args.index_csv}\nContexts dir: {args.contexts_dir}")


if __name__ == "__main__":
    main()
