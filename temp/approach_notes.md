Initial strategy for FinanceQA (Costco 10-K)

Dataset columns of interest (based on prompt):
- question
- answer
- context: large dump from Costco 10-K relevant sections
- context_link: SEC URL to filing (if provided in dataset)
- question_type: conceptual, assumption, basic

General challenges
- Long contexts: The context column can be very large, often exceeding typical context windows.
- Mixed reasoning: Some items are direct lookup (basic), others require conceptual understanding or validating assumptions.
- Grounding: Answers should be grounded strictly in the provided filing context.

Overall pipeline (initial design)
1) Preprocess context
   - Chunk by semantic units (e.g., sections, headings) with overlap, maintain metadata (section headers, page numbers if available).
   - Build both sparse (BM25) and dense embeddings (e.g., bge-large-en, e5-large) for hybrid retrieval.
2) Query understanding
   - Classifier or simple heuristic using question_type when available; otherwise, train a lightweight router to predict type.
   - Extract key entities and numeric targets (e.g., "membership revenue", period, fiscal year).
3) Retrieval
   - Use hybrid retrieval to get top-k chunks (k≈3–8) based on the query + extracted entities/time.
   - For numeric queries, bias retrieval toward tables and MD&A sub-sections.
4) Reasoning & answering
   - For short answers: use an extractive QA head (span extraction) or constrained generation.
   - For reasoning: use program-aided reasoning (calculate with Python) and citation generation.
   - For assumption validation: entailment checks against context (NLI-style) and contradiction detection.
5) Verification
   - Self-consistency: multiple sampled reasoning traces with agreement check.
   - Rule-based validators for numbers: units, signs, time period alignment, footnote/adjustment detection.
6) Output
   - Final answer + supporting quotes/snippets from the context; optionally the SEC link.

Type-specific approaches
- Basic
  - Nature: direct lookup questions (definitions, single figures, explicit statements in text).
  - Approach: high-precision retrieval to one or two chunks; apply extractive QA or short-form generation with copying bias.
  - Techniques: span extraction model, pointer-generator bias, quote-and-answer format.
  - Guardrails: ensure the extracted span exists verbatim in retrieved text; include citation lines.

- Conceptual
  - Nature: understanding relationships, qualitative interpretations, or policy/strategy descriptions.
  - Approach: multi-chunk retrieval with query-focused summarization; structured outline prompting (What, Why, How, Implications) grounded in quotes.
  - Techniques: chain-of-thought internally; externally present concise rationale with 2–3 supporting quotes. Use section-aware retrieval (MD&A, Risk Factors).
  - Guardrails: require at least two corroborating snippets; check for period mismatch and boilerplate that could mislead.

- Assumption
  - Nature: questions propose a claim—must verify if supported by context.
  - Approach: convert claim to hypotheses; run textual entailment (entails/contradicts/neutral) against retrieved chunks. If numerical, compute from tables and compare.
  - Techniques: NLI classifier (deberta-v3-large-mnli or finance-tuned), rule-based numeric comparator with tolerance and unit detection.
  - Guardrails: if evidence is insufficient or contradictory, answer "Not supported by the filing"; attach contrary evidence quotes.

Handling long context
- Pre-chunk to ~800–1200 tokens with 15% overlap; index both sparse and dense.
- Routing: if query is numeric, prefer table-containing chunks (detect via markup or regex density of numbers).
- If top-k exceeds model window, do reranking (cross-encoder) and assemble a focused context under limit.

Evaluation plan (short-term)
- Load a small batch (5–20) and compute baseline accuracies per type using a simple RAG (BM25 + LLM extractive answer). 
- Track: exact match (normalized), F1 for token overlap, and a entailment-based correctness score.
- Record citations (chunk IDs + text spans) for error analysis.

Next steps
- Implement a minimal retriever + answerer scaffold.
- Add an assumption verifier (NLI) component.
- Expand to table-aware numeric extraction and calculation.
