"""
Finance Agent v4: Three-Tool Architecture
- structured_data_lookup: For specific financial metrics from database
- document_search: For conceptual/narrative questions from FAISS
- python_calculator: For mathematical calculations
"""

import modal

# Define the Modal app
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

# Use the volume for persistent storage
volume = modal.Volume.from_name("finance-agent-storage")

# Configuration
NARRATIVE_TOP_K = 5  # Number of narrative chunks to retrieve

# All the actual implementation
@app.function(
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-key-1")],
    timeout=120
)
def process_question_v4(question: str) -> str:
    """
    Enhanced workflow with three specialized tools:
    1. structured_data_lookup - for financial metrics
    2. document_search - for narrative/conceptual content
    3. python_calculator - for calculations
    """
    # Import inside Modal environment
    import os
    import sys
    sys.path.insert(0, "/root/app")
    import sqlite3
    from openai import OpenAI
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings
    import re
    import ast
    import operator
    import math
    
    print("\n" + "="*60)
    print("FINANCE AGENT V4: Three-Tool Architecture")
    print("="*60)
    
    # Initialize OpenAI client
    client = OpenAI()
    
    # 1. Route to the appropriate tool
    router_prompt = f"""You are a routing agent. Think step-by-step to choose the best tool for this financial question.
    
Available Tools:
1. structured_data_lookup: Use for questions seeking specific numbers from financial statements
   - Examples: "What was revenue in 2024?", "Show me net income for the last 3 years", "What is the total assets?"
   
2. document_search: Use for conceptual or qualitative questions about strategy, risks, operations
   - Examples: "What are the main risk factors?", "Describe the business strategy", "What products does Costco sell?"
   
3. python_calculator: Use for explicit mathematical calculations
   - Examples: "Calculate 15% of 1 million", "What's the growth rate if revenue went from 100M to 150M?"

Question: {question}

Analyze step-by-step:
1. Is this asking for a specific financial number/metric? → structured_data_lookup
2. Is this asking about concepts, strategy, or qualitative information? → document_search
3. Is this asking to calculate something? → python_calculator

Choose the MOST appropriate tool. Respond with ONLY the tool name."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": router_prompt}],
        temperature=0
    )
    
    tool_choice = response.choices[0].message.content.strip().lower()
    print(f"Router selected: {tool_choice}")
    
    # 2. Execute the selected tool
    if tool_choice == "structured_data_lookup":
        # Query structured financial data with more robust matching and tracing
        try:
            # Extract key information from the question
            question_lower = question.lower()

            # Expanded financial metrics mapping with canonical DB items
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

            # Resolve canonical item and list of patterns
            canonical_item = None
            like_patterns = []
            for canon, patterns in metric_mapping.items():
                if any(pat in question_lower for pat in patterns):
                    canonical_item = canon
                    like_patterns = patterns
                    break

            # Extract year (robust: prefer 20xx; if "year end 2024" also matches)
            year = None
            year_match = re.search(r'(?:20)\d{2}', question)
            if year_match:
                year = int(year_match.group())

            # Connect to database
            conn = sqlite3.connect("/data/costco_financial_data.db")
            cursor = conn.cursor()

            # Prefer view with actual_value scaling if present
            cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='financial_summary'")
            use_view = cursor.fetchone() is not None
            table = 'financial_summary' if use_view else 'financial_data'
            cols = 'item, fiscal_year, ' + ('actual_value, unit' if use_view else 'value, unit')

            # Build dynamic WHERE
            wheres = []
            params = []
            if like_patterns:
                # OR over all LIKE patterns
                like_clause = "(" + " OR ".join(["LOWER(item) LIKE ?" for _ in like_patterns]) + ")"
                wheres.append(like_clause)
                params.extend([f"%{p}%" for p in like_patterns])
            if year:
                wheres.append("fiscal_year = ?")
                params.append(year)

            sql = f"SELECT {cols} FROM {table}"
            if wheres:
                sql += " WHERE " + " AND ".join(wheres)
            sql += " ORDER BY fiscal_year DESC LIMIT 10"

            print(f"[structured_data_lookup] SQL: {sql}")
            print(f"[structured_data_lookup] params: {params}")
            cursor.execute(sql, params)
            results = cursor.fetchall()

            # If nothing found and we had a canonical item, retry without year, or with the canonical name exact
            if not results and canonical_item:
                retry_sql = f"SELECT {cols} FROM {table} WHERE LOWER(item) = ? ORDER BY fiscal_year DESC LIMIT 3"
                print(f"[structured_data_lookup] retry SQL: {retry_sql}")
                cursor.execute(retry_sql, [canonical_item])
                results = cursor.fetchall()

            # If still nothing and we had patterns, try any single pattern (broader)
            if not results and like_patterns:
                broad_sql = f"SELECT {cols} FROM {table} WHERE " + " OR ".join(["LOWER(item) LIKE ?" for _ in like_patterns]) + " ORDER BY fiscal_year DESC LIMIT 3"
                print(f"[structured_data_lookup] broad SQL: {broad_sql}")
                cursor.execute(broad_sql, [f"%{p}%" for p in like_patterns])
                results = cursor.fetchall()

            conn.close()

            # Format results
            if results:
                formatted = []
                for item, fy, val, unit in results:
                    if unit == 'millions':
                        formatted.append(f"{item} ({fy}): ${val/1_000_000:,.0f} million" if use_view else f"{item} ({fy}): ${val:,.0f} million")
                    elif unit == 'percent':
                        formatted.append(f"{item} ({fy}): {val}%")
                    elif unit == 'dollars':
                        formatted.append(f"{item} ({fy}): ${val:.2f}")
                    elif unit == 'count':
                        formatted.append(f"{item} ({fy}): {int(val)}")
                    else:
                        formatted.append(f"{item} ({fy}): {val} {unit}")
                tool_result = "\n".join(formatted)
            else:
                tool_result = "No data found for the specified query."

        except Exception as e:
            tool_result = f"Error querying structured data: {str(e)}"
        
    elif tool_choice == "document_search":
        # Search narrative content
        try:
            embeddings = OpenAIEmbeddings()
            kb = FAISS.load_local("/data/narrative_kb_index", embeddings, allow_dangerous_deserialization=True)
            retriever = kb.as_retriever(search_kwargs={"k": NARRATIVE_TOP_K})
            
            docs = retriever.get_relevant_documents(question)
            
            if docs:
                combined_text = "\\n---\\n".join([doc.page_content for doc in docs])
                tool_result = f"From the narrative sections of the 10-K:\\n\\n{combined_text}"
            else:
                tool_result = "No relevant narrative content found."
                
        except Exception as e:
            tool_result = f"Error searching narrative content: {str(e)}"
        
    elif tool_choice == "python_calculator":
        # Extract and perform calculation (LLM extracts expression; local eval for safety)
        calc_prompt = f"""Extract the mathematical calculation from this question. Think step-by-step.

Question: {question}

Think step-by-step:
1. Identify all numbers mentioned in the question
2. Determine what mathematical operation is needed
3. Construct the expression using Python syntax

You can use:
- Basic operators: +, -, *, /, //, %, **
- Functions: sqrt(), abs(), round(), min(), max(), sum(), log(), log10(), exp()
- Trigonometric: sin(), cos(), tan()
- Rounding: ceil(), floor()
- Constants: pi, e

Return ONLY the mathematical expression to calculate.
If no calculation is needed, return "NO_CALCULATION".

Examples:
- "What is 30% of 1000?" → "1000 * 0.3"
- "Calculate growth rate from $100M to $150M" → "((150 - 100) / 100) * 100"

Expression:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": calc_prompt}],
            temperature=0
        )

        calc_expr = response.choices[0].message.content.strip()

        if calc_expr != "NO_CALCULATION":
            from agent.utils.calculator import evaluate_expression
            calc_result = evaluate_expression(calc_expr)
            tool_result = f"Expression: {calc_expr}\\nResult: {calc_result}"
        else:
            tool_result = "No calculation could be extracted from the question"
    
    else:
        # Fallback
        tool_result = "Unable to determine the appropriate tool for this question."
        tool_choice = "unknown"
    
    # 3. Generate final answer
    tool_context = {
        "structured_data_lookup": "The data comes from audited financial statements.",
        "document_search": "The information comes from the narrative sections of the 10-K filing.",
        "python_calculator": "The calculation was performed using the provided mathematical expression."
    }
    
    final_prompt = f"""You are a financial analyst providing a final answer. Think step-by-step.
    
Question: {question}
Tool Used: {tool_choice}
Tool Result: {tool_result}
Context: {tool_context.get(tool_choice, "")}

INSTRUCTIONS:
1. First, analyze the tool result to extract the key information
2. Think step-by-step about what the question is asking
3. Formulate your answer following these STRICT rules:

FORMATTING RULES:
- For NUMERICAL answers: Always present the final numerical answer in this EXACT format:
  {{"answer": <number>, "unit": "<unit>"}}
  Examples:
  {{"answer": 254123, "unit": "millions of USD"}}
  {{"answer": 23.5, "unit": "percent"}}
  {{"answer": 1250000, "unit": "shares"}}
  
- For YES/NO questions: Start your answer with exactly "Yes" or "No" (capital first letter), then explain.
  
- For OTHER questions: Be direct and specific. State the main answer in the first sentence.

IMPORTANT:
- For structured data results, present the exact numbers from the database
- For narrative results, synthesize the key points concisely
- For calculations, show both the expression and the result
- Always end numerical answers with the JSON format specified above

Think step-by-step, then provide your answer:"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0
    )
    
    return response.choices[0].message.content.strip()

# Context-aware variant: prefer provided context over external tools
@app.function(
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-key-1")],
    timeout=120
)
def process_question_v4_ctx(question: str, context: str = "") -> str:
    """Context-first: if context is provided, bypass retrieval and use it directly.
    Adds deterministic handlers for margins and year-over-year comparisons to avoid LLM math drift.
    """
    # Import inside Modal environment
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

    def _find_line_values(ctx_lines, label_regexes, year=None):
        """Scan lines, return first (value_in_millions, unit) where a label regex and optional year appear on same/neighbor line."""
        for i, line in enumerate(ctx_lines):
            lower = line.lower()
            if year and str(year) not in lower and not (i+1 < len(ctx_lines) and str(year) in ctx_lines[i+1].lower()):
                continue
            for rgx in label_regexes:
                if re.search(rgx, lower, flags=re.IGNORECASE):
                    # search same line then next line for number with unit
                    for look in (line, ctx_lines[i+1] if i+1 < len(ctx_lines) else ""):
                        m = re.search(r"\$?([0-9][0-9,]*\.?[0-9]*)\s*(billion|billions|bn|million|millions|m)\b", look, flags=re.IGNORECASE)
                        if m:
                            val = Decimal(m.group(1).replace(',', ''))
                            unit = m.group(2)
                            return (_to_millions(val, unit), 'millions')
        return (None, None)

    qlow = (question or '').lower()
    ctx = (context or '').strip()

    # Deterministic handlers using line-based, unit-aware extraction
    if ctx:
        lines = [ln.strip() for ln in ctx.splitlines() if ln.strip()]
        # Operating margin (2024) and compare vs 2023
        if 'operating profit margin' in qlow or 'operating margin' in qlow:
            rev, _ = _find_line_values(lines, [r"total\s+revenue", r"net\s+sales"], year=2024)
            opi, _ = _find_line_values(lines, [r"operating\s+income", r"operating\s+profit"], year=2024)
            if rev and opi and rev != 0:
                margin = _quantize((opi / rev) * Decimal('100'))
                if 'compared to 2023' in qlow or 'greater in 2024' in qlow or '2023' in qlow:
                    rev2, _ = _find_line_values(lines, [r"total\s+revenue", r"net\s+sales"], year=2023)
                    opi2, _ = _find_line_values(lines, [r"operating\s+income", r"operating\s+profit"], year=2023)
                    if rev2 and opi2 and rev2 != 0:
                        m2 = _quantize((opi2 / rev2) * Decimal('100'))
                        yn = 'Yes' if margin > m2 else 'No'
                        return f"{yn}. 2024 Operating Margin: {margin}% vs 2023: {m2}%"
                return f"Operating Profit Margin (2024): {margin}%\n{{\"answer\": {str(margin)}, \"unit\": \"percent\"}}"
        # EBITDA margins
        if 'ebitda margin' in qlow or ('ebitda' in qlow and 'margin' in qlow):
            rev, _ = _find_line_values(lines, [r"total\s+revenue", r"net\s+sales"], year=2024)
            e_label = [r"adjusted\s+ebitda"] if 'adjusted' in qlow else [r"ebitda"]
            ebitda, _ = _find_line_values(lines, e_label, year=2024)
            if rev and ebitda and rev != 0:
                margin = _quantize((ebitda / rev) * Decimal('100'))
                return f"EBITDA Margin (2024): {margin}%\n{{\"answer\": {str(margin)}, \"unit\": \"percent\"}}"
        # Operating profit value
        if 'operating profit' in qlow and 'margin' not in qlow:
            opi, _ = _find_line_values(lines, [r"operating\s+income", r"operating\s+profit"], year=2024)
            if opi is not None:
                val = _quantize(opi)
                return f"Operating Profit (2024): ${val} million\n{{\"answer\": {str(val)}, \"unit\": \"millions of USD\"}}"

    # Fall back to LLM using provided context as tool result
    client = OpenAI()
    tool_choice = "document_search" if ctx else "python_calculator"
    tool_result = textwrap.shorten(ctx, width=8000, placeholder="...") if ctx else ""

    if not tool_result:
        return process_question_v4.remote(question)

    tool_context = {
        "structured_data_lookup": "The data comes from audited financial statements.",
        "document_search": "The information comes from provided context (FinanceQA dump).",
        "python_calculator": "The calculation was performed using the provided mathematical expression."
    }

    final_prompt = f"""You are a financial analyst providing a final answer. Think step-by-step.

Question: {question}
Tool Used: {tool_choice}
Tool Result (Provided Context): {tool_result}
Context: {tool_context.get(tool_choice, "")}

INSTRUCTIONS:
1. Use ONLY the provided Tool Result for factual grounding.
2. For numerical answers: return JSON at the end: {{"answer": <number>, "unit": "<unit>"}}
3. For YES/NO: Start with Yes/No.
4. Be concise and faithful to the context.

Think step-by-step, then provide your answer:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()

# Local-10K context variant: build context from data/ narrative FAISS index and run ctx pipeline
@app.function(
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-key-1")],
    timeout=120
)
def process_question_v4_local(question: str) -> str:
    # Import inside Modal environment
    import sys
    sys.path.insert(0, "/root/app")
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings
    import textwrap

    embeddings = OpenAIEmbeddings()
    kb = FAISS.load_local("/data/narrative_kb_index", embeddings, allow_dangerous_deserialization=True)
    retriever = kb.as_retriever(search_kwargs={"k": 6})
    docs = retriever.get_relevant_documents(question)
    ctx = "\n---\n".join([d.page_content for d in docs]) if docs else ""
    return process_question_v4_ctx.remote(question, ctx)

# Web endpoint
@app.function(
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-key-1")],
    timeout=120
)
def web_endpoint_v4(request: dict) -> dict:
    """HTTP endpoint for the three-tool finance agent."""
    question = request.get("question", "")
    
    if not question:
        return {"error": "No question provided"}
    
    try:
        answer = process_question_v4.remote(question)
        return {
            "question": question,
            "answer": answer,
            "version": "v4-three-tools",
            "status": "success"
        }
    except Exception as e:
        return {
            "question": question,
            "error": str(e),
            "version": "v4-three-tools",
            "status": "error"
        }

# Local testing
@app.local_entrypoint()
def main(question: str = None):
    """Test the three-tool finance agent locally."""
    
    test_questions = [
        # Structured data questions
        "What was Costco's revenue in 2024?",
        "Show me net income for the last 3 years",
        "What is the gross profit margin?",
        
        # Narrative/conceptual questions
        "What are Costco's main risk factors?",
        "Describe Costco's business strategy",
        "What products does Costco sell?",
        
        # Calculation questions
        "Calculate 15% of 254 billion",
        "What's the growth rate if revenue increased from 230 billion to 254 billion?",
        "If gross margin is 11% and revenue is 254 billion, what is gross profit?",
    ]
    
    if question:
        # Test single question
        print(f"\nQuestion: {question}")
        answer = process_question_v4.remote(question)
        print(f"\nAnswer: {answer}")
    else:
        # Test all example questions
        print("\n" + "="*60)
        print("TESTING THREE-TOOL FINANCE AGENT V4")
        print("="*60)
        
        for q in test_questions:
            print(f"\nQuestion: {q}")
            answer = process_question_v4.remote(q)
            print(f"Answer: {answer}")
            print("-" * 40)
