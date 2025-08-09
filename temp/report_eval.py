#!/usr/bin/env python3
import argparse
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def read_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                rows.append(json.loads(s))
    return rows


def safe_pct(num, den):
    if not den:
        return "-"
    return f"{100.0 * num/den:.1f}%"


def summarize(rows):
    by_type = defaultdict(lambda: {
        "n": 0,
        "em": 0,
        "f1_sum": 0.0,
        "span_ok": 0,
        "span_n": 0,
        "num_ok": 0,
        "num_n": 0,
        "verify": defaultdict(int),
    })
    for r in rows:
        t = r.get("question_type", "unknown")
        bt = by_type[t]
        bt["n"] += 1
        bt["em"] += int(r.get("exact_match", 0))
        bt["f1_sum"] += float(r.get("f1", 0.0))
        if r.get("span_supported") is not None:
            bt["span_n"] += 1
            bt["span_ok"] += int(bool(r.get("span_supported")))
        if r.get("numeric_close") is not None:
            bt["num_n"] += 1
            bt["num_ok"] += int(bool(r.get("numeric_close")))
        if r.get("verify_label"):
            bt["verify"][r["verify_label"]] += 1
    return by_type


def make_report(rows, dataset_name, out_path):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    by_type = summarize(rows)

    lines = []
    lines.append(f"# FinanceQA Evaluation Report\n")
    lines.append(f"Generated: {ts}\n")
    lines.append(f"Dataset: {dataset_name}\n")
    lines.append("")

    # Summary table
    lines.append("## Summary by question_type\n")
    lines.append("type | n | EM | EM% | F1 avg | span% | numeric% | verify dist")
    lines.append("--- | ---: | ---: | ---: | ---: | ---: | ---: | ---")
    for t, v in by_type.items():
        n = v["n"]
        em = v["em"]
        f1_avg = (v["f1_sum"]/n) if n else 0.0
        span_pct = (100.0 * v["span_ok"]/v["span_n"]) if v["span_n"] else None
        num_pct = (100.0 * v["num_ok"]/v["num_n"]) if v["num_n"] else None
        verify = ", ".join(f"{k}:{c}" for k, c in v["verify"].items()) if v["verify"] else "-"
        lines.append(
            f"{t} | {n} | {em} | {safe_pct(em, n)} | {f1_avg:.3f} | "
            f"{('-' if span_pct is None else f'{span_pct:.1f}%')} | "
            f"{('-' if num_pct is None else f'{num_pct:.1f}%')} | {verify}"
        )

    # Detailed section
    lines.append("\n## Detailed results\n")
    for t in sorted(set(r.get("question_type", "unknown") for r in rows)):
        lines.append(f"### {t}\n")
        subset = [r for r in rows if r.get("question_type")==t]
        for r in subset:
            q = r.get("question", "").strip()
            gold = (r.get("gold_answer") or "").strip()
            pred = (r.get("model_answer") or "").strip()
            em = int(r.get("exact_match", 0))
            f1 = r.get("f1", 0.0)
            span = r.get("span_supported")
            numc = r.get("numeric_close")
            ver = r.get("verify_label")
            lines.append("- id: " + str(r.get("id")))
            lines.append("  question: " + q)
            lines.append("  gold: " + gold)
            lines.append("  pred: " + pred)
            lines.append(f"  metrics: EM={em}, F1={f1:.3f}, span={span}, numeric_close={numc}, verify={ver}")
            lines.append("")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote report to {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="temp/eval_simple_results_10.jsonl")
    ap.add_argument("--dataset", default="FinanceQA 10-sample")
    ap.add_argument("--out", default="dump/eval_report_10.md")
    args = ap.parse_args()

    rows = read_jsonl(args.results)
    make_report(rows, args.dataset, args.out)


if __name__ == "__main__":
    main()
