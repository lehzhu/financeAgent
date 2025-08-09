# FinanceQA Agent

A pragmatic baseline for answering finance questions using three simple tools (SQLite lookups, FAISS narrative search, and a safe calculator). Current measured accuracy on FinanceQA (v4) ranges from ~30–50% depending on sample size and question mix. Branches v4.5 and v5 were experiments and are not as mature.

## Quick Demo

```bash
Q: "What was Costco's revenue in 2024?"
A: "Costco's total revenue in 2024 was $254,123 million."
   {"answer": 254123, "unit": "millions of USD"}
```

## The Architecture: Three Specialized Tools

📊 **SQL Database** → Financial metrics queries (67% accurate)  
📚 **Document Search** → Narrative/conceptual questions (100% accurate)  
🧮 **Safe Calculator** → Mathematical calculations (0% - needs work)

Base GPT-4o-mini = 11% accuracy  
Three specialized tools = 50% accuracy (355% improvement)

## Quick Start

### 1. Setup
```bash
# Clone and install
git clone <repo>
cd financeAgent
pip install -r requirements.txt

# Add OpenAI key
echo "OPENAI_API_KEY=sk-..." > .env

# Setup data in Modal
modal run setup_modal_db.py
modal run setup_narrative_index.py
```

### 2. Deploy
```bash
pip install modal
modal setup  # First time only
modal deploy agent/finance_agent_v4_deploy.py
```

### 3. Ask Questions
```bash
modal run agent/finance_agent_v4_deploy.py "What was the gross margin?"
```

## Evaluate v4

Prerequisites:
- Modal CLI installed and authenticated: `modal setup`
- OpenAI secret in Modal (needed for routing and final formatting):
  ```bash
  modal secret create openai-key-1 OPENAI_API_KEY=sk-...  # do this once
  ```
- Data available in the Modal volume:
  ```bash
  modal run setup_modal_db.py
  modal run setup_narrative_index.py
  ```
- v4 agent deployed (so the evaluator can call the remote function):
  ```bash
  modal deploy agent/finance_agent_v4_deploy.py
  ```

Run evaluation:
- Quick smoke test (3 questions):
  ```bash
  modal run test/evaluate_v4.py::evaluate_agent_v4 --test-size 3
  ```
- Small sample (e.g., 20 random questions):
  ```bash
  modal run test/evaluate_v4.py::evaluate_agent_v4 --test-size 20
  ```

## Documentation

- Overview and version history: docs/ARCHITECTURE.md

## Performance

| Model | Accuracy | Notes |
|-------|----------|-------|
| Base GPT-4o | 11% | January 2025 baseline |
| v4 Three-Tool | 50% | Current best, 355% improvement |

### By Question Type (v4):
- Narrative: 100% accuracy
- Structured Data: 67% accuracy  
- Calculations: 0% accuracy (needs improvement)

## Project Structure

```
agent/
  finance_agent_v4_deploy.py  # The three-tool agent
  main_v4_new.py             # Original implementation
  
data/
  costco_financial_data.db   # SQLite database
  costco_narrative.txt       # Narrative text
  
test/
  evaluate_v4.py            # Run accuracy tests
  
setup_modal_db.py          # Upload DB to Modal
setup_narrative_index.py   # Build FAISS index
  
docs/
  README.md          # Complete guide
  ARCHITECTURE.md    # How it works
  PRD.md            # Our story
```

## Current Status 

- The current v4 baseline works end-to-end but is inconsistent across question types.
- Narrative/qualitative questions perform relatively well; structured lookups are decent when the metric is present.
- The calculation path is weak (often 0% on calc-heavy subsets) due to unreliable expression extraction.
- Branches v4.5 and v5 did not reach a stable or better-performing state; they are considered failed experiments.
- No promises: use this repo as a starting point, not a production solution.

## Roadmap toward ~80% accuracy

Concrete, incremental steps you can implement here to materially improve accuracy (especially calculations):

1) Deterministic calculator for finance tasks (highest impact)
   - Replace LLM-based expression extraction with a rule-based parser for common patterns:
     - Margins (operating, gross, EBITDA), growth rates (YoY/ QoQ), percentage-of, CAGR, ratio math
   - Use Decimal for math and return strict JSON (value + units)
   - Add unit-aware helpers (convert million/billion; percent vs ratio) and fail fast on ambiguity

2) Strict I/O contract everywhere
   - Enforce JSON outputs for all tools and the final answer (number + units + optional trace)
   - Centralize unit normalization before comparisons; add tolerance-aware verification (bp/relative)

3) Router hardening (simple and effective)
   - Heuristic rules + small keyword model to reduce misroutes (calc vs structured vs narrative)
   - Add a fallback: if calc parse fails, try structured lookup for inputs, then recompute deterministically

4) Expand and normalize the SQLite metrics
   - Ingest more line items (D&A, interest, memberships, warehouse count, etc.) with clear units
   - Create a financial_summary view with normalized actual_value for consistent math

5) Evaluation discipline
   - Keep a small, stratified smoke set (calc/structured/narrative) and run in CI
   - Store evaluation dumps with per-type breakdown and diff against last run


---

