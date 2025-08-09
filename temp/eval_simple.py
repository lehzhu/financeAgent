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
import csv
import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Dict, Any, Iterable, List

DEFAULT_INPUT = "data/financeqa_50.jsonl"
DEFAULT_INDEX_CSV = "data/financeqa_50_index.csv"
DEFAULT_OUTPUT = "temp/eval_simple_results.jsonl"
DEFAULT_ENV = ".env"

# OpenRouter model names; override via env vars if desired.
MODEL_BASIC = os.getenv("OPENROUTER_MODEL_BASIC", "google/gemini-2.5-flash")
MODEL_THINKING = os.getenv("OPENROUTER_MODEL_THINKING", "google/gemini-2.5-flash-thinking")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def normalize_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def build_prompt(example: Dict[str, Any], focused_ctx: str = None) -> Dict[str, Any]:
    q = example.get("question") or ""
    a = example.get("answer") or ""
    ctx = focused_ctx if focused_ctx is not None else (example.get("context") or "")
    qtype = (example.get("question_type") or "basic").lower()

    if qtype == "conceptual":
        system = (
            "You are a finance expert. Answer the conceptual question concisely. "
            "Do not use the filing context. Provide a brief rationale."
        )
        user = f"Question: {q}\nAnswer concisely."
        return {"system": system, "user": user, "use_context": False}

    # basic and assumption must use filing; ask for extractive format
    must_cite = (
        "Use ONLY the provided 10-K snippets below. Answer by copying an exact span from the snippets. "
        "Output STRICTLY in this format on two lines:\n"
        "ANSWER: <copied exact phrase or number>\n"
        "CITATION: \"<short supporting quote from the snippets>\"\n"
        "If not supported, output exactly: ANSWER: Not supported by the filing"
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

    user = (
        f"Question: {q}\n\n10-K snippets (do not summarize; copy exact answer):\n{ctx}\n\n"
        "Rules:\n"
        "- Answer by copying exactly from the snippets.\n"
        "- If multiple candidates, choose the shortest that fully answers.\n"
        "- Do not add extra commentary.\n"
        "Respond in the required format."
    )
    return {"system": system, "user": user, "use_context": True}

def or_request(model: str, system: str, user: str, api_key: str) -> str:
    req = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    data = json.dumps(req).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://local.eval",
        "X-Title": "FinanceQA Simple Eval",
    }
    request = urllib.request.Request(OPENROUTER_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=90) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return ""
    choices = payload.get("choices") or []
    if not choices:
        return ""
    msg = choices[0].get("message") or {}
    return msg.get("content") or ""


def load_env_file(path: str) -> None:
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        v = v.strip().strip("\"\'")
        if k and v and k not in os.environ:
            os.environ[k] = v


def iter_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def iter_index_csv(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def load_examples(args) -> List[Dict[str, Any]]:
    examples: List[Dict[str, Any]] = []
    if args.index_csv and os.path.exists(args.index_csv):
        # Lightweight rows; load context lazily later
        for row in iter_index_csv(args.index_csv):
            examples.append(row)
        return examples
    # Fallback to JSONL
    for ex in iter_jsonl(args.input):
        examples.append(ex)
    return examples


def get_context_for_example(ex: Dict[str, Any], args) -> str:
    # If using index CSV, load from file path when needed
    if args.index_csv and "context_path" in ex and ex.get("context_path"):
        try:
            with open(ex["context_path"], "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""
    # Else from JSONL
    return ex.get("context") or ""


# ---------------- Retrieval utilities ----------------

def simple_tokenize_for_index(s: str) -> List[str]:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return [t for t in s.split() if t]


def chunk_text(text: str, target_chars: int = 1000, overlap: int = 150) -> List[str]:
    if not text:
        return []
    # Prefer paragraph chunks by double newline; then merge to target size
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    chunks: List[str] = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) + 2 <= target_chars:
            current = (current + "\n\n" + p) if current else p
        else:
            if current:
                chunks.append(current)
            # if single paragraph is too big, split by length
            if len(p) > target_chars:
                for i in range(0, len(p), max(1, target_chars - overlap)):
                    chunks.append(p[i:i + target_chars])
                current = ""
            else:
                current = p
    if current:
        chunks.append(current)
    if not chunks:
        # Fallback to fixed-size chunks
        for i in range(0, len(text), max(1, target_chars - overlap)):
            chunks.append(text[i:i + target_chars])
    return chunks


def build_tfidf(chunks: List[str]):
    # Compute DF and IDF
    N = len(chunks)
    dfs: Dict[str, int] = {}
    chunk_tokens: List[List[str]] = []
    for ch in chunks:
        toks = simple_tokenize_for_index(ch)
        chunk_tokens.append(toks)
        seen = set(toks)
        for t in seen:
            dfs[t] = dfs.get(t, 0) + 1
    idf: Dict[str, float] = {}
    for t, df in dfs.items():
        idf[t] = max(0.0, __import__("math").log((N + 1) / (df + 1)) + 1)
    return chunk_tokens, idf


def tf(tokens: List[str]) -> Dict[str, float]:
    d: Dict[str, float] = {}
    for t in tokens:
        d[t] = d.get(t, 0.0) + 1.0
    # l2 normalize later
    return d


def cosine_dict(a: Dict[str, float], b: Dict[str, float]) -> float:
    import math
    dot = 0.0
    for k, v in a.items():
        if k in b:
            dot += v * b[k]
    na = math.sqrt(sum(v*v for v in a.values())) or 1.0
    nb = math.sqrt(sum(v*v for v in b.values())) or 1.0
    return dot / (na * nb)


def is_numeric_query(q: str) -> bool:
    q = (q or "").lower()
    if re.search(r"[0-9$%]", q):
        return True
    keywords = [
        "revenue", "sales", "income", "profit", "earnings", "eps", "margin",
        "increase", "decrease", "growth", "decline", "yoy", "year-over-year",
        "operating", "gross", "net", "cash", "capex", "membership", "comparable",
        "same-store", "ratio", "percentage", "percent"
    ]
    return any(k in q for k in keywords)


def number_density_score(text: str) -> float:
    # Score based on count of digits normalized by length
    if not text:
        return 0.0
    digits = sum(ch.isdigit() for ch in text)
    return digits / max(50, len(text))  # normalize to avoid over-weighting long texts


def looks_like_table(text: str) -> bool:
    # Heuristic: multiple lines with 3+ numbers or presence of many delimiters
    lines = (text or "").splitlines()
    count_num_lines = 0
    for ln in lines:
        nums = len(re.findall(r"[0-9][0-9,\.]*", ln))
        if nums >= 3:
            count_num_lines += 1
        if count_num_lines >= 2:
            return True
    return False


def retrieve_top_k(query: str, chunks: List[str], k: int = 10) -> List[str]:
    qtoks = simple_tokenize_for_index(query)
    chunk_tokens, idf = build_tfidf(chunks)
    # Build TF-IDF vectors as dicts
    def tfidf(tokens: List[str]) -> Dict[str, float]:
        vec = {}
        for t in tokens:
            if t in idf:
                vec[t] = vec.get(t, 0.0) + idf[t]
        return vec
    qvec = tfidf(qtoks)
    numeric_q = is_numeric_query(query)
    scores = []
    for ch, toks in zip(chunks, chunk_tokens):
        cvec = tfidf(toks)
        base = cosine_dict(qvec, cvec)
        bonus = 0.0
        if numeric_q:
            bonus += 0.2 * number_density_score(ch)
            if looks_like_table(ch):
                bonus += 0.05
        scores.append((base + bonus, ch))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scores[:k]]


# ---------------- Scoring utilities ----------------

def tokenize(s: str) -> List[str]:
    s = (s or "").lower()
    # Keep alphanumerics and %/$/., split on others
    cleaned = re.sub(r"[^a-z0-9%$\.\-]+", " ", s)
    return [t for t in cleaned.split() if t]


def f1_score(pred: str, gold: str) -> float:
    p = tokenize(pred)
    g = tokenize(gold)
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    common = {}
    for tok in p:
        common[tok] = common.get(tok, 0) + 1
    overlap = 0
    for tok in g:
        if common.get(tok, 0) > 0:
            overlap += 1
            common[tok] -= 1
    if overlap == 0:
        return 0.0
    precision = overlap / len(p)
    recall = overlap / len(g)
    return 2 * precision * recall / (precision + recall)


def span_supported_by_context(answer_text: str, context: str) -> bool:
    if not answer_text or not context:
        return False
    return normalize_text(answer_text) in normalize_text(context)


def parse_answer_from_model(raw: str) -> str:
    # Expect ANSWER: ... possibly with surrounding spaces
    for line in (raw or "").splitlines():
        if line.strip().lower().startswith("answer:"):
            ans = line.split(":", 1)[1].strip()
            # Strip surrounding quotes
            if (ans.startswith('"') and ans.endswith('"')) or (ans.startswith("'") and ans.endswith("'")):
                ans = ans[1:-1].strip()
            # Strip trailing period
            if ans.endswith('.'):
                ans = ans[:-1]
            return ans.strip()
    return (raw or "").strip()


def try_parse_number(text: str):
    if text is None:
        return None
    s = text.strip().lower()
    # Handle parentheses negatives and currency/commas
    neg = False
    if s.startswith('(') and s.endswith(')'):
        neg = True
        s = s[1:-1]
    s = s.replace('$', '').replace(',', '').strip()
    is_percent = s.endswith('%')
    if is_percent:
        s = s[:-1].strip()
    try:
        val = float(s)
        if is_percent:
            # Treat percent as percentage number, not ratio (e.g., 5% -> 5.0)
            pass
        if neg:
            val = -val
        return (val, 'percent' if is_percent else 'number')
    except Exception:
        return None


def numeric_close(pred: str, gold: str, rel_tol: float = 0.005, abs_tol: float = 1e-6) -> bool:
    pp = try_parse_number(pred)
    gg = try_parse_number(gold)
    if not pp or not gg:
        return False
    pv, pu = pp
    gv, gu = gg
    if pu != gu:
        # Allow comparison if one is ratio form (e.g., 0.05) and other percent (5)
        if pu == 'percent' and gu != 'percent':
            pv = pv / 100.0
        elif gu == 'percent' and pu != 'percent':
            gv = gv / 100.0
    import math
    if math.isfinite(pv) and math.isfinite(gv):
        if abs(pv - gv) <= max(abs_tol, rel_tol * max(1.0, abs(gv))):
            return True
    return False


# ---------------- Main ----------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to JSONL sample (fallback)")
    parser.add_argument("--index_csv", default=DEFAULT_INDEX_CSV, help="Path to compact index CSV (preferred)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--env", default=DEFAULT_ENV, help="Path to .env file (default .env)")
    args = parser.parse_args()

    if args.env:
        load_env_file(args.env)

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to your .env or export it before running.")

    examples = load_examples(args)

    results = []
    for ex in examples:
        # Ensure expected keys exist
        qtype = (ex.get("question_type") or "basic").lower()
        ex = dict(ex)  # copy
        if qtype in ("basic", "assumption") and ("context" not in ex or not ex.get("context")):
            ex["context"] = get_context_for_example(ex, args)

        # Retrieval: focus context for basic/assumption
        focused_ctx = None
        retrieved_chunks = []
        if qtype in ("basic", "assumption"):
            chunks = chunk_text(ex.get("context") or "")
            retrieved_chunks = retrieve_top_k(ex.get("question") or "", chunks, k=6)
            # Join with separators and indices for clarity
            focused_ctx = "\n\n".join(f"[SNIPPET {i+1}]\n{c}" for i, c in enumerate(retrieved_chunks))

        prompt = build_prompt(ex, focused_ctx)

        # Route model
        if qtype == "conceptual":
            model_name = MODEL_THINKING  # thinking ON
        elif qtype == "assumption":
            model_name = MODEL_THINKING  # thinking ON
        else:
            model_name = MODEL_BASIC     # thinking OFF

        # Fallbacks in case a specific model isn't available to this key
        fallback_map = {
            MODEL_THINKING: ["google/gemini-2.0-flash-thinking-exp", "google/gemini-1.5-pro"],
            MODEL_BASIC: ["google/gemini-2.0-flash", "google/gemini-1.5-flash"],
        }

        raw = or_request(model_name, prompt["system"], prompt["user"], api_key).strip()
        if not raw:
            for alt in fallback_map.get(model_name, []):
                raw = or_request(alt, prompt["system"], prompt["user"], api_key).strip()
                if raw:
                    break

        # Post-process
        pred_ans = parse_answer_from_model(raw) if qtype in ("basic", "assumption") else raw
        gold = ex.get("answer") or ""
        em = int(normalize_text(pred_ans) == normalize_text(gold))
        f1 = f1_score(pred_ans, gold)
        span_ok = span_supported_by_context(pred_ans, ("\n\n".join(retrieved_chunks) if retrieved_chunks else (ex.get("context") or ""))) if qtype in ("basic", "assumption") else None
        num_ok = numeric_close(pred_ans, gold)

        # Assumption verifier pass
        verifier = None
        if qtype == "assumption":
            verify_system = (
                "You are a strict verifier. Decide if the CLAIM is supported by the 10-K snippets. "
                "Output exactly one of: entails, contradicts, insufficient. Then provide one short quote."
            )
            verify_user = (
                f"CLAIM: {ex.get('question') or ''}\n\n10-K snippets:\n{focused_ctx or ex.get('context') or ''}\n\n"
                "Respond with one word label (entails/contradicts/insufficient) on the first line, then QUOTE: \"...\""
            )
            verifier_raw = or_request(MODEL_THINKING, verify_system, verify_user, api_key).strip()
            lab = verifier_raw.splitlines()[0].strip().lower() if verifier_raw else ""
            if lab.startswith("entail"):
                verifier = "entails"
            elif lab.startswith("contradict") or lab.startswith("refute"):
                verifier = "contradicts"
            else:
                verifier = "insufficient"

        results.append({
            "id": ex.get("id"),
            "question_type": qtype,
            "question": ex.get("question"),
            "gold_answer": gold,
            "model_answer_raw": raw,
            "model_answer": pred_ans,
            "exact_match": em,
            "f1": f1,
            "span_supported": span_ok,
            "numeric_close": num_ok,
            "verify_label": verifier,
        })

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as out:
        for r in results:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Print a quick summary
    by_type = {}
    for r in results:
        t = r["question_type"]
        by_type.setdefault(t, {"n": 0, "em": 0, "f1_sum": 0.0, "span_ok": 0, "span_n": 0, "num_ok": 0, "num_n": 0, "verify": {}})
        by_type[t]["n"] += 1
        by_type[t]["em"] += r["exact_match"]
        by_type[t]["f1_sum"] += r.get("f1", 0.0)
        if r.get("span_supported") is not None:
            by_type[t]["span_n"] += 1
            by_type[t]["span_ok"] += int(bool(r["span_supported"]))
        if r.get("numeric_close") is not None:
            by_type[t]["num_n"] += 1
            by_type[t]["num_ok"] += int(bool(r["numeric_close"]))
        if r.get("verify_label"):
            lab = r["verify_label"]
            by_type[t]["verify"][lab] = by_type[t]["verify"].get(lab, 0) + 1

    summary = {}
    for t, v in by_type.items():
        summary[t] = {
            "n": v["n"],
            "em": v["em"],
            "em_rate": (v["em"] / v["n"] if v["n"] else 0),
            "f1_avg": (v["f1_sum"] / v["n"] if v["n"] else 0.0),
            "span_support_rate": (v["span_ok"] / v["span_n"] if v["span_n"] else None),
            "numeric_close_rate": (v["num_ok"] / v["num_n"] if v["num_n"] else None),
            "verify_distribution": v["verify"],
        }

    print(json.dumps({"output": args.output, "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
