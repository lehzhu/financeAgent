#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List

# Minimal retrieval copied from evaluator to reproduce snippets

def simple_tokenize_for_index(s: str):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return [t for t in s.split() if t]


def chunk_text(text: str, target_chars: int = 1000, overlap: int = 150):
    if not text:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    chunks: List[str] = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) + 2 <= target_chars:
            current = (current + "\n\n" + p) if current else p
        else:
            if current:
                chunks.append(current)
            if len(p) > target_chars:
                for i in range(0, len(p), max(1, target_chars - overlap)):
                    chunks.append(p[i:i + target_chars])
                current = ""
            else:
                current = p
    if current:
        chunks.append(current)
    if not chunks:
        for i in range(0, len(text), max(1, target_chars - overlap)):
            chunks.append(text[i:i + target_chars])
    return chunks


def build_tfidf(chunks: List[str]):
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
    import math
    for t, df in dfs.items():
        idf[t] = max(0.0, math.log((N + 1) / (df + 1)) + 1)
    return chunk_tokens, idf


def cosine_dict(a: Dict[str, float], b: Dict[str, float]) -> float:
    import math
    dot = 0.0
    for k, v in a.items():
        if k in b:
            dot += v * b[k]
    na = math.sqrt(sum(v*v for v in a.values())) or 1.0
    nb = math.sqrt(sum(v*v for v in b.values())) or 1.0
    return dot / (na * nb)


def retrieve_top_k(query: str, chunks: List[str], k: int = 6) -> List[str]:
    qtoks = simple_tokenize_for_index(query)
    chunk_tokens, idf = build_tfidf(chunks)
    def tfidf(tokens: List[str]) -> Dict[str, float]:
        vec = {}
        for t in tokens:
            if t in idf:
                vec[t] = vec.get(t, 0.0) + idf[t]
        return vec
    qvec = tfidf(qtoks)
    scores = []
    for ch, toks in zip(chunks, chunk_tokens):
        cvec = tfidf(toks)
        scores.append((cosine_dict(qvec, cvec), ch))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scores[:k]]


def read_index_csv(path: str):
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def read_jsonl(path: str):
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if s:
                rows.append(json.loads(s))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--index_csv', default='data/financeqa_10_index.csv')
    ap.add_argument('--results', default='temp/eval_simple_results_10.jsonl')
    ap.add_argument('--out', default='dump/diagnose_10.md')
    ap.add_argument('--limit', type=int, default=10)
    args = ap.parse_args()

    index_rows = read_index_csv(args.index_csv)
    results_rows = read_jsonl(args.results)

    # Map by id for results
    res_by_id = {str(r.get('id')): r for r in results_rows}

    lines = []
    lines.append('# Manual Diagnosis Report\n')
    lines.append('This report shows question, gold, model outputs, and top retrieved snippets.\n')

    count = 0
    for item in index_rows:
        if count >= args.limit:
            break
        ex_id = str(item.get('id'))
        qtype = (item.get('question_type') or '').lower()
        q = item.get('question') or ''
        gold = item.get('answer') or ''
        ctx_path = item.get('context_path') or ''
        ctx = ''
        try:
            if ctx_path and os.path.exists(ctx_path):
                ctx = Path(ctx_path).read_text(encoding='utf-8')
        except Exception:
            ctx = ''

        res = res_by_id.get(ex_id, {})
        raw = (res.get('model_answer_raw') or '').strip()
        pred = (res.get('model_answer') or '').strip()
        em = int(res.get('exact_match', 0))
        f1 = res.get('f1', 0.0)
        span = res.get('span_supported')
        numc = res.get('numeric_close')
        ver = res.get('verify_label')

        # Retrieve snippets only for basic/assumption
        snippets = []
        if qtype in ('basic', 'assumption'):
            chunks = chunk_text(ctx)
            snippets = retrieve_top_k(q, chunks, k=6)

        lines.append(f'## id: {ex_id} | type: {qtype}\n')
        lines.append(f'- Question: {q}')
        lines.append(f'- Gold: {gold}')
        lines.append(f'- Pred (parsed): {pred}')
        lines.append(f'- Raw model output:')
        lines.append('')
        lines.append('```')
        lines.append(raw)
        lines.append('```')
        lines.append(f'- Metrics: EM={em}, F1={f1:.3f}, span={span}, numeric_close={numc}, verify={ver}')
        if snippets:
            lines.append('- Retrieved snippets:')
            for i, s in enumerate(snippets, start=1):
                lines.append(f'  - [SNIPPET {i}]')
                # Truncate long snippet for readability
                text = s.strip()
                preview = text if len(text) <= 1200 else text[:1200] + '...'
                lines.append('')
                lines.append('```')
                lines.append(preview)
                lines.append('```')
        lines.append('')
        count += 1

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Wrote diagnosis to {outp}')


if __name__ == '__main__':
    main()
