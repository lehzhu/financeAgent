# FinanceAgent – Architecture & Design Outline

## Agent Summary

**Purpose**:  
Answer questions about Costco's 10-K using best-available open or API-based language models. Handles both fact lookups (e.g. "What is revenue?"), conceptual/qualitative questions about the business ("What risks are listed?"), and calculations.

**Interfaces**:  
- Plain natural language question (typed or API)
- Structured JSON answer for numerical queries (e.g. `{ "answer": 254123, "unit": "millions USD" }`)

**Environment**:  
- Production: Modal cloud (API key gated)
- Local: N/A (not in V4) 

---

## Current System Design (as of v4)

**Routing**  
A GPT-4o prompt classifies every question into one of three routes:
- Structured data (metric lookup)
- Conceptual/narrative (search/semantic retrieval)
- Calculation

**Metric Lookup**  
- Fetches exact numbers from an up-to-date SQLite DB built from 10-K tables only.
- Nearly zero latency and high trustworthiness.

**Narrative Retrieval**  
- Uses FAISS + OpenAI embeddings, but indexes only "narrative" prose from filings (no tables).
- Returns the five most relevant text chunks for relevant questions (risks, strategy, etc).

**Calculations**  
- Extracts and safely evaluates mathematical expressions using Python's AST parser.
- Only allows safe arithmetic and whitelisted functions.

**Formatting**  
- All numerical/metric answers include a JSON snippet to disambiguate units and values.
- Final output for each tool is passed through a formatting agent for tone/clarity.

---

## Key Choices and Trade-offs

1. **Routing before retrieval**  
   - Why: Putting everything through RAG results in poor recall for structure and slow inference.
   - Trade-off: Requires a high-quality prompt and some complexity in maintenance.

2. **Separate DB for metrics, FAISS for narrative**  
   - Why: Numbers are best fetched directly, not reranked. Narrative is too complex/varied for SQL.
   - Trade-off: Two pipelines; must keep both in sync when filings update.

3. **JSON format for key answers**  
   - Why: LLM output is ambiguous for numbers ("254 billion", "$254,000,000,000", "about 254B"), which harms downstream evaluation.
   - Trade-off: Slightly higher token cost and formatting failures if not handled carefully.

4. **AST Calculator**  
   - Why: Simple `eval()` is unsafe and hard to restrict. AST allows safe, predictable eval of only allowed math.
   - Trade-off: Some functions/operators (e.g. custom statistics, string manipulation) are not allowed.

---

## Results & Benchmarking

- **FinanceQA benchmark accuracy**: Typically 85–90% exact match on structured + calculation; 80–85% for qualitative narrative.
- **Latency**: All routes finish in under 3 seconds per question 95% of the time.
- **Cost per query**: $0.01–0.03 with current OpenAI API; much lower if running locally with Ollama, but model quality is lower.
- **Token usage**:
    - Metrics: under 500
    - Narrative: about 1,500–2,000
    - Calculation: < 100

**Failure modes**:  
- Router occasionally misclassifies "synthetic" questions (e.g., multi-part or ambiguous), harming recall.
- FAISS fails when summarizing unknown/new risks/sections not present in top-5 chunks.
- Calculation tool limited to arithmetic and whitelisted math.

---

## What's Next?

**Planned improvements**:
- ZeroEntropy reranker integration (for narrative search, to beat OpenAI embeddings or local FAISS ranking).
- Modal/Ollama "turbo" support for both local-LLM and hybrid cloud execution.
- More general search: Expand narrative index to include cross-document, multi-filings, and potentially peer comparisons ("How did Costco's profit vs. Walmart's?").
- Self-evaluation agent: Output not just an answer, but a confidence/reasoning trace (and suggest when model is not confident).
- Assumption engine: Infer reasonable numbers or disclaimers when data is missing or ambiguous.
- Unified logging and error reporting to better analyze failure modes in each pipeline.

---

**Contact or contribute**:  
- Add metric: Update DB and tool mapping  
- Add function: Whitelist in calculator  
- Add document: Update narrative text, re-index  
- Issues/feedback: [See repository](../README.md)  

---
