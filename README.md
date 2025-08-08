# FinanceAgent v5

A from-scratch, test-driven rewrite focused on answering real finance questions with transparency.

What v5 is
- Deterministic where possible (calculator, database lookups, calculated metrics)
- Transparent evaluation (unified test runner with curated FinanceQA-style questions)
- Incremental phases so we always know what works and what doesn’t

Current capabilities
- Phase 1: Calculator (100%)
  - Basic arithmetic, percentages, growth rates, ratios
- Phase 2: Costco Financial Data (100%)
  - Total revenue, net sales, net income, operating income (from SQLite DB)
- Phase 3: Calculation + Data (100%)
  - Profit margin (Net Income / Total Revenue * 100)
  - Operating margin (Operating Income / Total Revenue * 100)
  - Revenue growth (YoY)
- Phase 4: Narrative (Not implemented yet)
  - Business strategy, risk factors, conceptual questions

Repository layout (v5)
- v5/main.py                Minimal router (Costco → data/metrics, else calculator)
- v5/phase1_calculator.py   Deterministic AST-based calculator
- v5/phase2_costco_data.py  SQLite-backed Costco data agent (no hard-coded paths)
- v5/phase3_metrics.py      Calculated metrics using Phase 2 data
- v5/curated_tests.py       Human-readable test questions and expectations
- v5/test_all.py            Unified transparent test runner

Data
- Uses data/costco_financial_data.db
  - Path resolution order: explicit db_path arg > FINANCEAGENT_DB env var > default relative path

Run it
- Ask a question
  - python3 v5/main.py --question "What was Costco's total revenue in 2024?"
- Run all tests
  - python3 v5/test_all.py

Design principles
- Keep business logic simple and explicit
- Prefer DB and math over LLMs for structured questions
- Add LLMs only where they add value (Phase 4 narrative, routing fallbacks)

What’s next
- Phase 4 (Narrative): retrieval + LLM summarization with citations
- Expand schema and coverage (additional metrics/years)
- Optional LLM router/normalizer behind environment flags

# FinanceQA Agent

A multi-agent system for answering financial questions using specialized tools. Currently achieving 50% accuracy on the FinanceQA dataset (v4), up from 11% with base GPT-4o.

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

## Documentation

📖 **[How it Works](docs/README.md)** - Start here for the full guide  
🏗️ **[Architecture](docs/ARCHITECTURE.md)** - Technical deep dive  
📈 **[Our Journey](docs/PRD.md)** - How we went from 46% to 90%

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

- ✅ 50% accuracy achieved (up from 11% baseline)
- ✅ Three-tool architecture deployed on Modal
- ✅ Excellent narrative search (100% accuracy)
- ⚠️ Calculator tool needs fixing (0% accuracy)
- 🚧 Target: 90% accuracy

## Contributing

1. **Fix calculator** - Main priority, currently at 0%
2. **Add metrics** - Expand the SQLite database
3. **Improve routing** - Better tool selection logic

---

