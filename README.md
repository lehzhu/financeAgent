# FinanceAgent

Purpose
- Answer Costco finance questions via deterministic tools with predictable outputs.
- Three operational phases:
  1) Calculator (math/percentages/ratios)
  2) Structured data lookups (SQLite)
  3) Calculated metrics (margins, growth) from the same DB
- Narrative retrieval is planned but not required for core operation.

What’s new (data ingestion + schema)
- Auto-ingest 10-K content into SQLite for denser, year-aware coverage.
- Expanded schema with aliases, units, source, and notes; plus a financial_summary view that normalizes numeric scales.
- Non-deprecated Modal setup flow: build DB locally, then upload to the Modal volume.

Quick start
- Ask a question locally (set FINANCEAGENT_DB if using a custom path)
  - python3 agent/finance_agent_v4_deploy.py  # see @app.local_entrypoint
- Health checks (examples)
  - "What was Costco's net income in 2024?"
  - "What is the growth rate from 100 to 120?"

Configuration
- Environment variables
  - FINANCEAGENT_DB: absolute or relative path to the SQLite database
    - Default: data/costco_financial_data.db (resolved relative to repository root)
- Optional local setup
  - pip install -r requirements.txt (only needed for tooling scripts and optional setup)

Data ingestion
- Script: data/ingest_costco_10k.py
  - Inputs: data/costco_10k_full.txt, data/costco_10k_summary.txt
  - Extracts metrics via targeted regex/heuristics (e.g., Total Revenue, Gross Profit, Operating Income, Net Income, EPS, Total Assets, Total Liabilities, Equity, Cash, Inventory, Membership Fee Revenue, CapEx, Warehouse count).
  - Alias map canonicalizes item names to align with the agent’s metric mapping.
  - Autodetects additional CSV/JSON files by extension and ingests them if present.
  - Writes/updates data/costco_financial_data.db.

Database schema (expanded)
- Table: financial_data(
  - item TEXT, aliases TEXT, fiscal_year INTEGER, value REAL, unit TEXT,
  - source TEXT, note TEXT, period_type TEXT, is_computed INTEGER DEFAULT 0
)
- View: financial_summary
  - Adds actual_value (unit-normalized numeric) for easier comparisons and computed metrics.
- Rationale
  - Keep it simple and fast with SQLite; normalize units centrally; attach provenance via source/note.

Modal setup (DB provisioning)
- Flow (non-deprecated)
  1) Run ingestion locally to build data/costco_financial_data.db
  2) setup_modal_db.py uploads the DB to the Modal volume using add_local_file/add_local_dir
- Why this way
  - Local build gives predictable, testable artifacts; uploading a single DB file is less error-prone than mounting disparate inputs.

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
- Build or refresh the DB locally
  - python3 data/ingest_costco_10k.py
- Upload DB to Modal volume
  - python3 setup_modal_db.py
- Troubleshooting
  - DB not found: set FINANCEAGENT_DB to your DB path
  - Unexpected units: verify the unit column in financial_data and the financial_summary view
  - Year parsing: include a 4-digit year (e.g., 2024) or "fiscal/FY 2024"

Evaluation (optional)
- If you’re working on the v5 branch, there is an experimental evaluation runner. Example (Modal):
  - modal run evaluate_v5.py::run_eval --dataset-path hf:AfterQuery/FinanceQA --limit 10 --out-path /root/results/results.json

Documentation
- docs/ARCHITECTURE.md — runtime components, data flow, ingestion, and operational details
- docs/OPERATIONS.md — commands, configuration, schema DDL, troubleshooting

Rationale: three phases + Modal
- Deterministic core: calculator → data lookup → derived metrics. Clear separation makes behavior predictable and testable.
- Modal as the runner: reproducible environment and simple volumes; no secrets needed for the core. Add secrets only if you enable narrative/LLM later.
- Broader tradeoffs: we favor speed, simplicity, and auditability now (SQLite + heuristics). We can layer richer sources and Phase 4 narrative later without breaking the core.

Notes
- No external network calls are required to run the core app locally or on Modal.
- Deterministic code paths are used for phases 1–3; narrative features are optional and separate.

