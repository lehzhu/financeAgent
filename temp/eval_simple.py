#!/usr/bin/env python3
"""
Simple baseline evaluator over a local JSONL sample (default: data/financeqa_50.jsonl).

- Uses Gemini 2.5 Flash.
- question_type routing:
  * basic: use filing context; NO thinking mode
  * assumption: use filing context; thinking mode ON
  * conceptual: do NOT use filing context; thinking mode ON

Environment:
- Set GOOGLE_API_KEY in your environment. Do not hardcode secrets.

Outputs a JSONL with model answers and a simple exact-match metric.
"""
import argparse
import json
import os
import re
from typing import Dict, Any

import google.generativeai as genai

DEFAULT_INPUT = "data/financeqa_50.jsonl"
DEFAULT_OUTPUT = "temp/eval_simple_results.jsonl"

# Model names; thinking variants may differ by availability. You can override via env vars.
MODEL_BASIC = os.getenv("GEMINI_MODEL_BASIC", "gemini-2.5-flash")
MODEL_THINKING = os.getenv("GEMINI_MODEL_THINKING", "gemini-2.5-flash-thinking")


def normalize_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def build_prompt(example: Dict[str, Any]) -> Dict[str, Any]:
    q = example.get("question") or ""
    a = example.get("answer") or ""
    ctx = example.get("context") or ""
    qtype = (example.get("question_type") or "basic").lower()

    if qtype == "conceptual":
        system = (
            "You are a finance expert. Answer the conceptual question concisely. "
            "Do not use the filing context. Provide a brief rationale."
        )
        user = f"Question: {q}\nAnswer concisely."
        return {"system": system, "user": user, "use_context": False}

    # basic and assumption must use filing
    must_cite = (
        "Use ONLY the provided 10-K context below. Quote the exact supporting snippet(s). "
        "If not supported, say: 'Not supported by the filing.'"
    )
    if qtype == "assumption":
        system = (
            "You are an auditor validating claims against a 10-K filing. "
            + must_cite
        )
    else:
        system = (
            "You are an analyst answering questions strictly from a 10-K filing. "
            + must_cite
        )

    user = f"Question: {q}\n\n10-K context:\n{ctx}\n\nAnswer:"
    return {"system": system, "user": user, "use_context": True}


def call_model(model_name: str, system: str, user: str) -> str:
    model = genai.GenerativeModel(model_name=model_name, system_instruction=system)
    resp = model.generate_content(user)
    try:
        return resp.text or ""
    except Exception:
        return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set. Please export it before running.")
    genai.configure(api_key=api_key)

    results = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            ex = json.loads(line)
            prompt = build_prompt(ex)
            qtype = (ex.get("question_type") or "basic").lower()

            # Route model
            if qtype == "conceptual":
                model_name = MODEL_THINKING  # thinking ON
            elif qtype == "assumption":
                model_name = MODEL_THINKING  # thinking ON
            else:
                model_name = MODEL_BASIC     # thinking OFF

            answer_text = call_model(model_name, prompt["system"], prompt["user"]).strip()

            gold = ex.get("answer") or ""
            em = int(normalize_text(answer_text) == normalize_text(gold))

            results.append({
                "id": ex.get("id"),
                "question_type": qtype,
                "question": ex.get("question"),
                "gold_answer": gold,
                "model_answer": answer_text,
                "exact_match": em,
            })

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as out:
        for r in results:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Print a quick summary
    by_type = {}
    for r in results:
        t = r["question_type"]
        by_type.setdefault(t, {"n": 0, "em": 0})
        by_type[t]["n"] += 1
        by_type[t]["em"] += r["exact_match"]

    summary = {t: {"n": v["n"], "em": v["em"], "em_rate": (v["em"] / v["n"] if v["n"] else 0)} for t, v in by_type.items()}
    print(json.dumps({"output": args.output, "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
