"""
Evaluation script for context-first v4 agent using FinanceQA dataset context blocks.
"""

import modal
from datasets import load_dataset
import time
import json
import argparse

app = modal.App(
    "finance-evaluate-v4-ctx",
    image=modal.Image.debian_slim().pip_install("datasets")
)
volume = modal.Volume.from_name("finance-agent-storage")


def answers_match(expected, got, tolerance=0.02):
    if expected == got:
        return True
    # simple numeric extraction with tolerance
    import re
    def num(x):
        if x is None:
            return None
        xs = str(x)
        m = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", xs)
        if not m:
            return None
        try:
            return float(m[-1].replace(",", ""))
        except Exception:
            return None
    en = num(expected)
    gn = num(got)
    if en is not None and gn is not None:
        denom = max(abs(en), 0.01)
        return abs(en - gn) / denom < tolerance
    # yes/no containment
    el = str(expected).strip().lower()
    gl = str(got).strip().lower()
    if el in ["yes", "no"] and gl.startswith(el):
        return True
    # substring len>5
    return len(el) > 5 and el in gl


@app.function(volumes={"/data": volume}, timeout=1200)
def run_eval(test_size: int = 10, offset: int = 0, dump_path: str = "/data/eval_v4_ctx_results.json"):
    ds = load_dataset("AfterQuery/FinanceQA", split="test")
    n = min(test_size, len(ds) - offset)

    # Use context-first pipeline directly, bypassing retrieval; feed FinanceQA context blocks
    fn_ctx = modal.Function.from_name("finance-agent-v4-new", "process_question_v4_ctx")

    total = 0
    correct = 0

    print("="*60)
    print("FINANCE AGENT V4 – CONTEXT-FIRST EVALUATION")
    print(f"Testing {n} rows starting at offset {offset}")
    print("="*60)

    items = []
    for i in range(offset, offset + n):
        row = ds[i]
        q = row.get("question", "")
        ctx = row.get("context", "")
        exp = row.get("answer", "")
        t0 = time.time()
        try:
            ans = fn_ctx.remote(q, ctx)
        except Exception as e:
            ans = f"ERROR: {e}"
        dt = time.time() - t0

        total += 1
        ok = answers_match(exp, ans)
        if ok:
            correct += 1

        items.append({"id": i, "question": q, "expected": exp, "answer": ans, "ok": ok})

        print(f"[#{i}] Q: {q[:100]}...")
        print(f"Expected: {exp}")
        print(f"Got: {ans[:200]}..." if len(ans) > 200 else f"Got: {ans}")
        print(f"Match: {'✓' if ok else '✗'} | Time: {dt:.1f}s | Running Acc: {correct/total*100:.1f}%")
        print("-"*60)

    print("="*60)
    print(f"Final Accuracy: {correct}/{total} = {correct/total*100:.1f}%")
    print("="*60)

    # Write dump to /data
    with open(dump_path, "w") as f:
        json.dump({"total": total, "correct": correct, "accuracy": correct/total if total else 0.0, "items": items}, f, indent=2)
    print(f"Wrote results to {dump_path}")
    return {"dump_path": dump_path, "total": total, "correct": correct}

@app.local_entrypoint()
def main(test_size: int = 10, offset: int = 0, dump_path: str = "/data/eval_v4_ctx_results.json"):
    out = run_eval.remote(test_size, offset, dump_path)
    print(out)

