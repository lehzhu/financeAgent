# FinanceAgent

Purpose
- Answer Costco finance questions via deterministic tools with predictable outputs.
- Three operational phases:
  1) Calculator (math/percentages/ratios)
  2) Structured data lookups (SQLite)
  3) Calculated metrics (margins, growth) from the same DB
- Narrative retrieval is planned but not required for core operation.

Quick start
- Ask a question locally
  - python3 v5/main.py --question "What was Costco's total revenue in 2024?"
- Run the transparent test suite
  - python3 v5/test_all.py

Configuration
- Environment variables
  - FINANCEAGENT_DB: absolute or relative path to the SQLite database
    - Default: data/costco_financial_data.db (resolved relative to repository root)
- Optional local setup
  - pip install -r requirements.txt (only needed for tooling scripts and optional setup)

Database schema
- Table: financial_data(item TEXT, fiscal_year INTEGER, value REAL, unit TEXT)
- Example rows
  - ("Total Revenue", 2024, 254453, "millions")
  - ("Net Income", 2024, 7367, "millions")
  - ("Gross Margin", 2024, 13.0, "percent")

Routing behavior
- Mentions Costco + [margin|growth|growth rate] → Phase 3 (calculated metrics)
- Mentions Costco → Phase 2 (structured lookup)
- Otherwise → Phase 1 (calculator)

Response formatting
- Unit-aware formatting
  - millions → "$X million"; if ≥ 1000, convert to "$Y billion" with 1 decimal
  - percent → "X%"
  - dollars → "$X.YY"
- Year handling
  - If no year specified, default to latest year (assumed 2024)

Operations
- Health checks
  - python3 v5/main.py --question "What was Costco's net income in 2024?"
  - python3 v5/main.py --question "What is the growth rate from 100 to 120?"
- Test run
  - python3 v5/test_all.py (prints detailed per-question diagnostics)
- Troubleshooting
  - DB not found: set FINANCEAGENT_DB to your DB path
  - Unexpected units: verify the unit column in financial_data
  - Year parsing: include a 4-digit year (e.g., 2024) or "fiscal/FY 2024"

Documentation
- docs/ARCHITECTURE.md — runtime components, data flow, and operational details
- docs/OPERATIONS.md — commands, configuration, schema reference, troubleshooting

Notes
- No external network calls are required to run the core app locally.
- Deterministic code paths are used for phases 1–3; narrative features are optional and separate.

