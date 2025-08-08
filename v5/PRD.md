# FinanceAgent v5 - Internal PRD

Purpose
Build a transparent, test-driven finance agent focused on real business understanding (Costco) with incremental phases and deterministic accuracy where possible.

Non-goals
- Not a general chat agent
- Not LLM-first; we add LLMs only when they add value (Phase 4, routing fallback)

Scope (v5)
- Phase 1: Calculator (deterministic)
- Phase 2: Costco structured data via SQLite (deterministic)
- Phase 3: Calculated metrics from DB (deterministic)
- Phase 4: Narrative (retrieval + optional LLM)

Why this approach
- We want correctness, speed, and transparent failure modes
- Deterministic tools dominate FinanceQA-style accuracy for metrics and math
- LLMs help in narrative and ambiguous mapping, not arithmetic or exact DB lookups

Data
- Source: data/costco_financial_data.db (local SQLite)
- Access: relative path; override via FINANCEAGENT_DB env var

User stories
- As a user, I can ask: “What was Costco’s total revenue in 2024?” and get a precise number with the right units
- As a user, I can ask: “What was Costco’s profit margin in 2024?” and get a correct percentage computed from DB values
- As a maintainer, I can run one command and see exactly what works vs doesn’t

Acceptance criteria (current status)
- Phase 1 tests: 100% pass (basic arithmetic, percentage, growth, ratio)
- Phase 2 tests: 100% pass (revenue, sales, net income, operating income)
- Phase 3 tests: 100% pass (profit margin, operating margin, revenue growth)
- Phase 4: not implemented; tests are present and SKIP with clear messaging

Interfaces
- CLI (human): python3 v5/main.py --question "..."
- Tests (internal): python3 v5/test_all.py
- Env vars: FINANCEAGENT_DB

Routing
- If question mentions Costco + [margin|growth] → Phase 3
- Else if mentions Costco → Phase 2
- Else → Phase 1

Future work (Phase 4)
- Narrative retrieval (initially TF-IDF or embeddings) from costco_narrative.txt
- LLM summarization with short, cited answers
- Optional LLM router for ambiguous cases

Risks / Trade-offs
- Hard-coded patterns for routing may miss edge cases → mitigated by curated tests
- SQLite schema is minimal → expand as needed
- Narrative requires careful grounding → plan to constrain with retrieved context

KPIs
- Accuracy by phase (reported in test_all.py)
- Latency per question (log basic timings if needed)
- Cost (if/when LLMs introduced)

