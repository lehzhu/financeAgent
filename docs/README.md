# FinanceQA Agent Documentation

This documentation consolidates the evolution of the FinanceQA Agent across branches, highlighting decisions, tradeoffs, performance, and key mistakes. It also documents the best-performing architecture (v4) with actionable guidance.

- For a deep technical overview of v4, see ARCHITECTURE.md
- For the product/story context, see PRD.md

## Version History and Lessons

Below is a summary of each branch, the major changes, performance, tradeoffs, and common mistakes.

### v1-setup
- What we built: Single-function Modal app calling GPT-4o end-to-end; basic evaluation harness with “smart matching”.
- Performance: ~46.7% (smart matching) vs ~10% exact string; baseline target 56.8%.
- Tradeoffs: Simplicity and speed to first result; high token usage; limited determinism.
- Key mistakes:
  - Over-reliance on free-form LLM answers; formatting variance tanked exact-match scores.
  - Unit handling brittle (millions vs billions); occasional sign mistakes.
  - Evaluation initially leaned on tolerant matching, masking exact-match issues.

References: README.md, dump/evaluation_results.md, evaluate.py

### v2-agentic
- What we built: Early router + tools (parallel and sequential tests). Python calculator + doc search + QA fallback; Modal deployment notes.
- Performance: 40% reported (4/10); effectively ~50% after fixing a false negative; speedup 9.3x in parallel vs sequential for small batch.
- Tradeoffs: Lower cost via routing and tooling; complexity increased; retrieval quality inconsistent.
- Key mistakes:
  - String-matching evaluation caused false negatives (e.g., identical numbers, different formats).
  - Document retrieval recall inconsistent; balance-sheet specifics missed.
  - Calculator present but not consistently invoked or validated.

References: dump/v2_agentic_results.md, MODAL_DEPLOYMENT.md, ZEROENTROPY_INTEGRATION.md

### v3
- What we built: FAISS vector retrieval with smart filtering; optional ZeroEntropy reranking plan; cleaner project structure; benchmark/eval scripts.
- Performance: Still reported overall ~46.7% on sampled eval; improved token and latency efficiency (≈2k tokens, 2–3s per Q).
- Tradeoffs: Large token savings, speed; accuracy plateaued due to answer formatting and unit normalization issues.
- Key mistakes:
  - Optional reranking not fully operational; depended on pre-indexed collections not consistently set up.
  - Continued ambiguity in numerical output formatting preventing exact matches.

References: docs/CURRENT_VERSION.md, test/evaluate.py, dump/evaluation_results.md

### v3.5
- What we built: Stabilized v3 layout; deployed main agent with FAISS + smarter evaluation (JSON-aware extract_number). Still single-tool-ish path.
- Performance: Similar to v3 on accuracy; better evaluation robustness; foundation for multi-tool v4.
- Tradeoffs: Incremental changes; complexity kept moderate.
- Key mistakes:
  - No decisive architectural change to fix calculation correctness.
  - Reliance on LLM reasoning for numeric answers remained.

References: agent/main.py, test/evaluate.py

### v4 (best performing)
- What we built: Three specialized tools + router:
  1) Structured data lookup (SQLite) for financial metrics
  2) Narrative document search (FAISS) for conceptual questions
  3) Safe calculator (AST) for deterministic math
- Performance (eval_v4_threeTool, n=10): 50% overall; by category: narrative 100%, structured 66.7%, calculation 0% (needs work). Up from 11% base GPT‑4o-mini.
- Tradeoffs: Significant improvement via tool specialization and JSON outputs; router dependency and calculator weakness remained.
- Key mistakes:
  - Calculator path under-specified; extraction to expression failed on FinanceQA phrasing → 0% in that subset.
  - Inconsistent JSON formatting in some pathways; unit extraction still caused occasional scale errors.
  - Some duplication (deploy wrappers) caused confusion over deployed function names.

References: docs/ARCHITECTURE.md, dump/eval_v4_threeTool_2025-01-06_00-05.json, test/evaluate_v4.py, test/evaluate_multifaceted.py, agent/finance_agent_v4_deploy.py, agent/main_v4_new.py

### v4.5
- What we built: Simplified v4 with a single deploy entrypoint; context-first evaluation harness; local narrative FAISS indexing; ingestion pipeline for SQLite with schema/aliases; safer, deterministic margin math when context is provided.
- Performance: Context-first eval script and ingestion improved determinism; accuracy not summarized globally in repo, but operational reliability improved.
- Tradeoffs: Reduced external dependencies; bias toward determinism and auditability; optional LLM narrative.
- Key mistakes:
  - Calculator still not fully integrated with FinanceQA phrasing; router heuristics could misroute.
  - Fragmentation between context-first and tool-first paths increased maintenance overhead.

References: README.md (v4 simplified), agent/deploy.py, test/evaluate_v4_ctx.py, data/ingest_costco_10k.py, docs/ARCHITECTURE.md (v4.5)

### v5 (work-in-progress)
- What we built: A deterministic “Finance Math Engine” concept with rule-packs, strict JSON I/O, orchestrator/router skeleton, verification, grading, tolerance policies, EDGAR fetch plan.
- Performance: No end-to-end score yet; acceptance targets set (≥65% overall, ≥80% calc). Emphasis on fixing v4 calculator failure and assumptions.
- Tradeoffs: Bigger investment in tooling; reduced reliance on LLM for math/assumptions; more moving parts.
- Key mistakes (so far):
  - Structured lookup path is stubbed; narrative/filings integration not wired.
  - Requires router training or better heuristics.

References: v5/README.md, v5/documentation/internalPRD.md, v5/evaluate_v5.py, v5/agent/orchestrator.py

---

## Best Performing Architecture: v4 Summary

- Accuracy: 50% overall on sampled set; narrative 100%, structured 66.7%, calculation 0% (to fix)
- Cost: Router + final answer on GPT‑4o‑mini; tool calls are local/SQLite/FAISS
- Latency: Typically sub‑seconds per tool, dominated by LLM calls
- Key design:
  - Route to the best tool (structured, narrative, calc)
  - Use SQLite for exact numeric queries (unit-aware formatting)
  - Use FAISS for narrative retrieval
  - Use AST-based calculator for safety, but improve extraction
- Known failure modes:
  - Calculator extraction from natural language
  - JSON formatting consistency for numerical answers
  - Occasional unit scale mismatches

Action items to solidify v4:
- Replace LLM expression extraction with a deterministic parser for common finance tasks (growth rates, margins, YoY/ QoQ).
- Enforce strict JSON schema on final answers, including units.
- Harden unit normalization and introduce tolerance-aware verification.

---

## How to run v4

- Build Modal volumes: setup_modal_db.py, setup_narrative_index.py
- Deploy: modal deploy agent/finance_agent_v4_deploy.py
- Evaluate: modal run test/evaluate_v4.py or test/evaluate_multifaceted.py

See ARCHITECTURE.md for details.
