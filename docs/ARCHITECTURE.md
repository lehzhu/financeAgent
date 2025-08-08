# FinanceAgent — Architecture (Operational)

Purpose
- Provide deterministic, low-latency answers to Costco finance questions using three local tools.

Runtime overview
- Local-only core (no external network calls needed)
- Three agents + a keyword router:
  1) Calculator (safe AST arithmetic, percentages, growth rate, ratios)
  2) Structured data lookup (SQLite)
  3) Calculated metrics (margin, growth) using the same SQLite data

Components
- v5/main.py
  - CLI entrypoint and router
- v5/phase1_calculator.py
  - Safe AST evaluation; handlers for percentage-of, growth rate, simple ratios
- v5/phase2_costco_data.py
  - SQLite reader; maps question terms to DB items; year extraction; unit-aware formatting
- v5/phase3_metrics.py
  - Computes profit/operating margin and revenue growth; reuses Phase 2 data access
- v5/curated_tests.py and v5/test_all.py
  - Curated test cases and a transparent runner with per-phase reporting

Data model (SQLite)
- Table: financial_data(item TEXT, fiscal_year INTEGER, value REAL, unit TEXT)
- Units:
  - Financial metrics → "millions"
  - Percentages → "percent"
  - EPS → "per share"
- Example items: Total Revenue, Net Sales, Net Income, Operating Income, Merchandise Costs, Gross Margin, Membership Fee Revenue, Earnings Per Share Diluted

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

Extensibility
- Add a direct metric: extend field mapping in Phase 2
- Add a derived metric: implement compute path in Phase 3 using Phase 2 data
- Add coverage: insert new rows into financial_data with correct units

See also
- docs/OPERATIONS.md for commands, configuration, schema DDL, and troubleshooting
