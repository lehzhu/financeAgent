# FinanceAgent — Architecture (Operational)

FinanceAgent is a deterministic, three-phase system for answering Costco finance questions. It runs locally or on Modal without external calls for the core: Phase 1 performs calculator-style arithmetic, Phase 2 reads exact figures from a SQLite database, and Phase 3 computes derived metrics using the same data. A new ingestion pipeline loads 10-K content into an expanded SQLite schema (aliases, units, provenance, and a financial_summary view for normalized values). Modal is used for reproducible builds and simple volume persistence; secrets are only needed if an optional Phase 4 (narrative + LLM) is enabled. The design favors speed, simplicity, and auditability now, while leaving room to layer richer sources later.

Runtime overview
- Local-only core (no external network calls needed)
- Three agents + a keyword router:
  1) Calculator (safe AST arithmetic, percentages, growth rate, ratios)
  2) Structured data lookup (SQLite)
  3) Calculated metrics (margin, growth) using the same SQLite data

Components
- Agent runtime
  - agent/finance_agent_v4_deploy.py (Modal functions + local entrypoint)
  - agent/utils/calculator.py (shared safe AST calculator)
- Data ingestion
  - data/ingest_costco_10k.py (regex/heuristics + CSV/JSON autodetect)
  - data/schema.sql (DDL for tables and views)
- Ops
  - setup_modal_db.py (build DB locally, then upload to Modal volume via non-deprecated APIs)

Data model (SQLite)
- Tables
  - financial_data(
    item TEXT,
    aliases TEXT,
    fiscal_year INTEGER,
    value REAL,
    unit TEXT,
    source TEXT,
    note TEXT,
    period_type TEXT,
    is_computed INTEGER DEFAULT 0
  )
- Views
  - financial_summary: exposes actual_value (unit-normalized) for numeric comparisons and derived metrics
- Units
  - Financial metrics → "millions"
  - Percentages → "percent"
  - EPS → "per share"

Ingestion pipeline
- Inputs
  - data/costco_10k_full.txt, data/costco_10k_summary.txt
  - Optional CSV/JSON files (auto-detected by extension)
- Extraction
  - Targeted regex and light heuristics for common items (Total Revenue, Gross Profit, Operating Income, Net Income, EPS, Assets, Liabilities, Equity, Cash, Inventory, Membership Fee Revenue, CapEx, Warehouse count)
  - Alias mapping to canonical item names to match runtime metric mapping
- Normalization
  - Units standardized; financial_summary computes actual_value for consistent math
  - Source and note fields capture provenance and context
- Computed metrics
  - Marked with is_computed=1 when derived (e.g., margins); derived values are generated in the runtime but can be persisted if needed

Routing
- If question mentions Costco and [margin|growth|growth rate] → Phase 3
- If question mentions Costco → Phase 2
- Else → Phase 1

Control flow
- Phase 2: identify field → extract year (default latest) → SQL query → format
- Phase 3: identify metric → fetch required fields → compute → format percent

Error handling
- Unknown metric/field: return a helpful message
- Missing year: default to latest (assumed 2024)
- No DB row: return message indicating data absence
- Division-by-zero and None checks for derived metrics

Performance
- Typical local latency: sub-100ms
- Each question triggers a constant-time parse and a single query or arithmetic

Tradeoffs and rationale
- Three-phase design: keeps the core deterministic. Phase 1 (calculator), Phase 2 (structured lookup), and Phase 3 (derived metrics) are all local and predictable; Phase 4 (narrative + LLM) is optional and isolated so we can add it without destabilizing the core.
- Why Modal: reproducible builds, simple volumes for artifact persistence, and easy function-style entrypoints for both serving and evaluation. Phases 1–3 need no secrets, so Modal runs are clean and auditable; secrets are only attached if/when Phase 4 is enabled.
- Determinism vs. flexibility: we bias toward stable, testable outputs for finance questions. When flexibility is needed (free-form narrative), we turn on Phase 4 explicitly and track that dependency.
- SQLite over heavy parsers/XBRL: fast iteration for a single issuer; small operational surface area; easy to inspect and replace. We can graduate to richer sources later.
- Regex/heuristics vs. full parsing: pragmatic coverage for the common metrics now; CSV/JSON backstops let us fill gaps without retooling the parser.
- Single DB artifact: build locally, verify, then upload. This reduces runtime branching and surprises compared to piecemeal mounts.
- Aliases: map noisy item names to canonical keys so routing and queries stay stable across filings and wording changes.

Modal operational flow (at a glance)
- Build image with requirements → run ingestion locally → upload DB to Modal Volume → run function (router → Phase 1/2/3) → results persisted to volume if desired.

See also
- docs/OPERATIONS.md for commands, configuration, schema DDL, and troubleshooting
