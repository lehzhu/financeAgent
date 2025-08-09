"""
Finance Agent – Deploy (v4, simplified)
"""
# This file is a direct rename of finance_agent_v4_deploy.py to simplify naming.
# Content kept identical to previous deployed app.

import modal
import os

app = modal.App(
    "finance-agent-v4-new",
    image=(
        modal.Image.debian_slim()
        .pip_install(
            "langchain", "langchain-community", "langchain-openai",
            "faiss-cpu", "openai", "tiktoken"
        )
        .add_local_dir(os.path.dirname(os.path.dirname(__file__)), remote_path="/root/app")
    ),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

volume = modal.Volume.from_name("finance-agent-storage")
NARRATIVE_TOP_K = 5

@app.function(
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-key-1")],
    timeout=120
)
def process_question_v4(question: str) -> str:
    import sys, sqlite3, re, ast, operator, math
    sys.path.insert(0, "/root/app")
    from openai import OpenAI
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings

    client = OpenAI()
    router_prompt = f"You are a routing agent. Choose: structured_data_lookup | document_search | python_calculator.\nQuestion: {question}\nRespond with ONLY the tool name."
    tool_choice = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":router_prompt}], temperature=0).choices[0].message.content.strip().lower()

    if tool_choice == "structured_data_lookup":
        try:
            question_lower = question.lower()
            metric_mapping = {
                'total revenue': ['total revenue', 'net sales', 'revenue', 'sales'],
                'gross profit': ['gross profit'],
                'net income': ['net income', 'net earnings', 'profit'],
                'operating income': ['operating income', 'operating profit', 'ebit'],
                'earnings per share': ['earnings per share', 'eps', 'diluted eps', 'basic eps'],
                'total assets': ['total assets', 'assets'],
                'total liabilities': ['total liabilities', 'liabilities'],
                'stockholders equity': ['stockholders equity', 'equity', 'shareholders equity'],
                'cash and cash equivalents': ['cash and cash equivalents', 'cash'],
                'merchandise inventories': ['merchandise inventories', 'inventory'],
                'membership fee revenue': ['membership fee revenue', 'membership revenue']
            }
            canonical_item = None
            like_patterns = []
            for canon, pats in metric_mapping.items():
                if any(p in question_lower for p in pats):
                    canonical_item, like_patterns = canon, pats
                    break
            year = None
            m = re.search(r'(?:20)\d{2}', question)
            if m: year = int(m.group())
            conn = sqlite3.connect("/data/costco_financial_data.db")
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='financial_summary'")
            use_view = cur.fetchone() is not None
            table = 'financial_summary' if use_view else 'financial_data'
            cols = 'item, fiscal_year, ' + ('actual_value, unit' if use_view else 'value, unit')
            wheres, params = [], []
            if like_patterns:
                wheres.append("(" + " OR ".join(["LOWER(item) LIKE ?" for _ in like_patterns]) + ")")
                params.extend([f"%{p}%" for p in like_patterns])
            if year:
                wheres.append("fiscal_year = ?"); params.append(year)
            sql = f"SELECT {cols} FROM {table}" + (" WHERE " + " AND ".join(wheres) if wheres else "") + " ORDER BY fiscal_year DESC LIMIT 10"
            cur.execute(sql, params)
            rows = cur.fetchall()
            if not rows and canonical_item:
                cur.execute(f"SELECT {cols} FROM {table} WHERE LOWER(item)=? ORDER BY fiscal_year DESC LIMIT 3", [canonical_item])
                rows = cur.fetchall()
            if not rows and like_patterns:
                cur.execute(f"SELECT {cols} FROM {table} WHERE " + " OR ".join(["LOWER(item) LIKE ?" for _ in like_patterns]) + " ORDER BY fiscal_year DESC LIMIT 3", [f"%{p}%" for p in like_patterns])
                rows = cur.fetchall()
            conn.close()
            if rows:
                out = []
                for item, fy, val, unit in rows:
                    if unit == 'millions':
                        out.append(f"{item} ({fy}): ${val/1_000_000:,.0f} million" if use_view else f"{item} ({fy}): ${val:,.0f} million")
                    elif unit == 'percent': out.append(f"{item} ({fy}): {val}%")
                    elif unit == 'dollars': out.append(f"{item} ({fy}): ${val:.2f}")
                    elif unit == 'count': out.append(f"{item} ({fy}): {int(val)}")
                    else: out.append(f"{item} ({fy}): {val} {unit}")
                tool_result = "\n".join(out)
            else:
                tool_result = "No data found for the specified query."
        except Exception as e:
            tool_result = f"Error querying structured data: {e}"

    elif tool_choice == "document_search":
        try:
            embeddings = OpenAIEmbeddings()
            kb = FAISS.load_local("/data/narrative_kb_index", embeddings, allow_dangerous_deserialization=True)
            retriever = kb.as_retriever(search_kwargs={"k": NARRATIVE_TOP_K})
            docs = retriever.get_relevant_documents(question)
            tool_result = "\n---\n".join([d.page_content for d in docs]) if docs else "No relevant narrative content found."
        except Exception as e:
            tool_result = f"Error searching narrative content: {e}"
    else:
        # python_calculator handled via LLM extraction + local eval
        calc_prompt = f"Extract a Python expression to calculate: {question}. Return ONLY the expression or NO_CALCULATION."
        expr = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":calc_prompt}], temperature=0).choices[0].message.content.strip()
        if expr != "NO_CALCULATION":
            from agent.utils.calculator import evaluate_expression
            tool_result = f"Expression: {expr}\nResult: {evaluate_expression(expr)}"
        else:
            tool_result = "No calculation could be extracted from the question"

    final_prompt = f"You are a financial analyst.\nQuestion: {question}\nTool Used: {tool_choice}\nTool Result: {tool_result}\nFollow formatting rules and provide final answer."
    return client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":final_prompt}], temperature=0).choices[0].message.content.strip()

@app.function(
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-key-1")],
    timeout=120
)
def process_question_v4_ctx(question: str, context: str = "") -> str:
    import sys, re
    sys.path.insert(0, "/root/app")
    from decimal import Decimal, ROUND_HALF_EVEN
    from openai import OpenAI
    import textwrap

    def _quantize(x: Decimal, q='0.01'):
        return x.quantize(Decimal(q), rounding=ROUND_HALF_EVEN)

    def _to_millions(val: Decimal, unit: str) -> Decimal:
        unit = (unit or '').lower()
        if unit in ('billion','billions','bn'):
            return val * Decimal('1000')
        return val

    def _in_ops_section(ctx_lines, idx, back=10):
        start = max(0, idx - back)
        window = " ".join(l.lower() for l in ctx_lines[start:idx+1])
        return ("consolidated statements of operations" in window) or ("statements of operations" in window)

    def _find_line_values(ctx_lines, label_regexes, year=None, lookahead_lines=3, require_ops_section=False):
        for i, line in enumerate(ctx_lines):
            lower = line.lower()
            year_ok = True
            if year:
                year_ok = (str(year) in lower) or any(str(year) in (ctx_lines[j].lower() if j < len(ctx_lines) else "") for j in range(i+1, i+1+lookahead_lines))
            if not year_ok:
                continue
            if require_ops_section and not _in_ops_section(ctx_lines, i, back=10):
                continue
            for rgx in label_regexes:
                if re.search(rgx, lower, flags=re.IGNORECASE):
                    # search same line and up to N following lines
                    for j in range(i, min(i+1+lookahead_lines, len(ctx_lines))):
                        look = ctx_lines[j]
                        m = re.search(r"\$?([0-9][0-9,]*\.?[0-9]*)\s*(billion|billions|bn|million|millions|m)\b", look, flags=re.IGNORECASE)
                        if m:
                            val = Decimal(m.group(1).replace(',', ''))
                            unit = m.group(2)
                            return (_to_millions(val, unit), 'millions')
        return (None, None)

    qlow = (question or '').lower()
    ctx = (context or '').strip()

    if ctx:
        lines = [ln.strip() for ln in ctx.splitlines() if ln.strip()]
        if 'operating profit margin' in qlow or 'operating margin' in qlow:
            rev, _ = _find_line_values(lines, [r"total\s+revenue", r"net\s+sales"], year=2024, require_ops_section=True)
            opi, _ = _find_line_values(lines, [r"operating\s+income", r"operating\s+profit"], year=2024, require_ops_section=True)
            if rev and opi and rev != 0:
                margin = _quantize((opi / rev) * Decimal('100'))
                if 'compared to 2023' in qlow or 'greater in 2024' in qlow or '2023' in qlow:
                    rev2, _ = _find_line_values(lines, [r"total\s+revenue", r"net\s+sales"], year=2023, require_ops_section=True)
                    opi2, _ = _find_line_values(lines, [r"operating\s+income", r"operating\s+profit"], year=2023, require_ops_section=True)
                    if rev2 and opi2 and rev2 != 0:
                        m2 = _quantize((opi2 / rev2) * Decimal('100'))
                        yn = 'Yes' if margin > m2 else 'No'
                        return f"{yn}. 2024 Operating Margin: {margin}% vs 2023: {m2}%"
                return f"Operating Profit Margin (2024): {margin}%\n{{\"answer\": {str(margin)}, \"unit\": \"percent\"}}"
        if 'ebitda margin' in qlow or ('ebitda' in qlow and 'margin' in qlow):
            rev, _ = _find_line_values(lines, [r"total\s+revenue", r"net\s+sales"], year=2024, require_ops_section=True)
            # Try direct labels first
            if 'adjusted' in qlow:
                ebitda, _ = _find_line_values(lines, [r"adjusted\s+ebitda"], year=2024, require_ops_section=True)
            else:
                ebitda, _ = _find_line_values(lines, [r"ebitda"], year=2024, require_ops_section=True)
            # Fallback: compute from OI + D&A if needed
            if (not ebitda) and rev:
                oi, _ = _find_line_values(lines, [r"operating\s+income", r"operating\s+profit"], year=2024, require_ops_section=True)
                da, _ = _find_line_values(lines, [r"depreciation\s+and\s+amortization"], year=2024, lookahead_lines=5, require_ops_section=True)
                if oi is not None and da is not None:
                    ebitda = oi + da
            if rev and ebitda and rev != 0:
                margin = _quantize((ebitda / rev) * Decimal('100'))
                return f"EBITDA Margin (2024): {margin}%\n{{\"answer\": {str(margin)}, \"unit\": \"percent\"}}"
        if 'operating profit' in qlow and 'margin' not in qlow:
            opi, _ = _find_line_values(lines, [r"operating\s+income", r"operating\s+profit"], year=2024, require_ops_section=True)
            if opi is not None:
                val = _quantize(opi)
                return f"Operating Profit (2024): ${val} million\n{{\"answer\": {str(val)}, \"unit\": \"millions of USD\"}}"

    client = OpenAI()
    tool_result = textwrap.shorten(ctx, width=8000, placeholder="...") if ctx else ""
    if not tool_result:
        return process_question_v4.remote(question)
    final_prompt = f"You are a financial analyst.\nQuestion: {question}\nTool Used: document_search\nTool Result (Provided Context): {tool_result}\nFollow formatting rules and provide final answer."
    return client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":final_prompt}], temperature=0).choices[0].message.content.strip()

@app.function(
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-key-1")],
    timeout=120
)
def process_question_v4_local(question: str) -> str:
    import sys
    sys.path.insert(0, "/root/app")
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings

    embeddings = OpenAIEmbeddings()
    kb = FAISS.load_local("/data/narrative_kb_index", embeddings, allow_dangerous_deserialization=True)
    # Heuristic toggle: reduce k to 5 and disable strict year filtering
    retriever = kb.as_retriever(search_kwargs={"k": 5})
    docs = retriever.get_relevant_documents(question)
    # Note: previously preferred chunks containing the target year; disabled for recall
    ctx = "\n---\n".join([d.page_content for d in docs]) if docs else ""
    return process_question_v4_ctx.remote(question, ctx)
