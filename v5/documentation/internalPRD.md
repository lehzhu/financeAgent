# FinanceQA v5 Agent – Internal PRD 


**Last updated:** 2025‑08‑08\
**Status:** Draft 

---

## 1) Objective

Build a **cheap, reliable agent** that achieves **state‑of‑the‑art (or close)** accuracy on the FinanceQA benchmark by fixing two chronic failure modes:

1. **Numerical correctness** (replacing “calculator” with a deterministic **Finance Math Engine**).
2. **Accounting assumptions** (encoding common **rule‑packs** the LLM selects rather than invents).

Keep **GPT‑4o‑mini** (or similar small instruct model) as **orchestrator/router**; push math and accounting logic into tools. Maintain reproducibility and strict JSON outputs.

**Target KPI (acceptance):**

- ≥ **65% total accuracy** on FinanceQA official test set (overall)
- ≥ **80% accuracy** on *calculation* subset (post‑tolerance)
- Zero formatting failures (all answers parse as required JSON)

**Cost ceiling:** Orchestrator ≤ **\$0.01/question** at typical token counts.

---

## 2) Scope (v5)

**In scope**

- Deterministic **Finance Math Engine** with `Decimal` precision, unit normalization, and tolerance policy.
- **Assumption Rule‑Packs** (ASC 842 lease adjustments, SBC handling, one‑offs, TTM vs FY, diluted vs basic, etc.) to push through notoriously difficult Assumption Questions
- **Router** (classifier) to map question → {narrative | structured | calc | assumption‑calc}.
- **EDGAR/filing table access** from dataset links; table parser and alias map for line items.
- **Evaluation harness** with per‑type metrics and disagreement reports.
- **Answer formatter** enforcing exact schema and rationales.

**Out of scope (v5)**

- Web crawling beyond dataset‑provided links.
- RAG over arbitrary finance news.
- Agent UI.

---

## 3) User Story (internal)

“As an evaluation runner, I want the agent to answer FinanceQA questions with a **single JSON object** that includes a **final numeric/text answer**, a **transparent calc trace**, **assumptions applied**, and **source references**, so I can fairly grade, debug, and iterate.”

---

## 4) System Overview

**Orchestrator LLM (4o‑mini)** chooses tools and sequences calls. Math and accounting live in tools, not the model.

### 4.1 High‑Level Flow

1. **Router** classifies question → flow.
2. **Retrieval** (if needed): fetch filing tables/context via dataset link cache.
3. **Computation**: call **Finance Math Engine** with normalized units and aliases.
4. **Assumptions**: LLM picks applicable **rule‑packs** → engine applies adjustments.
5. **Verification**: dual‑path (lookup vs recompute). If disagree beyond tolerance, escalate.
6. **Formatter**: produce strict JSON with final answer + trace + sources.

### 4.2 Directory Structure

```
/financeAgent
  /agent
    orchestrator.py
    prompts/
    router/
      train_router.py
      router.pkl
  /tools
    finance_math.py
    units.py
    assumptions.py
    filings.py
    verifier.py
    formatters.py
    aliases.py
  /data
    financeqa.json
    edgar_cache/
  /eval
    evaluate.py
    grading.py
    tolerance_policies.json
    fixtures/
  /configs
    model.yaml
    logging.yaml
  /scripts
    run_eval.sh
    export_report.py
```

---

## 5) Interfaces (LLM Tool Schemas)

> All tools must be **function‑calling** compatible. Inputs/outputs are **strict JSON**. Numbers returned as **strings** that parse to Decimal (avoid float).

### 5.1 `fetch_filing_table`

- **purpose:** Load a specific table or section from cached EDGAR filing referenced by dataset.
- **input:**

```json
{
  "company": "string",
  "filing_link": "string",  
  "table_hint": "string",   
  "period": {"type": "FY|Q|TTM", "end": "YYYY-MM-DD"}
}
```

- **output:**

```json
{
  "units_hint": "USD|USD_thousands|USD_millions|percent",
  "table": [{"row": "string", "col": "string", "value": "string"}],
  "raw_text": "string"
}
```

### 5.2 `resolve_alias`

- **purpose:** Map natural language metric → canonical metric id and required line items.
- **input:** `{ "metric": "operating margin" }`
- **output:**

```json
{ "metric_id": "OPERATING_MARGIN", "requires": ["OPERATING_INCOME", "REVENUE"],
  "formula": "OPERATING_INCOME / REVENUE"
}
```

### 5.3 `normalize_units`

- **purpose:** Convert values to canonical base (USD) and consistent scale.
- **input:**

```json
{ "value": "string", "from_units": "USD_millions", "to_units": "USD",
  "percent": false }
```

- **output:** `{ "value": "string", "units": "USD" }`

### 5.4 `compute_formula`

- **purpose:** Deterministic finance computation using Decimal and a **formula registry**.
- **input:**

```json
{
  "metric_id": "EBITDA",
  "period": {"type":"FY|Q|TTM", "end":"YYYY-MM-DD"},
  "inputs": {"OPERATING_INCOME": "string", "DEPRECIATION": "string", "AMORTIZATION": "string"},
  "output_units": "USD|percent|ratio",
  "rounding": {"quantize": "0.01", "mode": "ROUND_HALF_EVEN"}
}
```

- **output:**

```json
{
  "value": "string",
  "trace": [
    {"op":"ADD","args":["OPERATING_INCOME","DEPRECIATION"],"result":"..."},
    {"op":"ADD","args":["<prev>","AMORTIZATION"],"result":"..."}
  ]
}
```

### 5.5 `apply_assumptions`

- **purpose:** Apply selected accounting rule‑packs.
- **input:**

```json
{
  "assumptions": ["ASC842_ADD_BACK", "EXCLUDE_SBC", "EXCLUDE_RESTRUCTURING"],
  "context": {"company":"string","period":{"type":"FY","end":"YYYY-MM-DD"}},
  "base_values": {"EBITDA":"string","OPERATING_LEASE_EXP":"string","SBC":"string","RESTRUCTURING":"string"}
}
```

- **output:**

```json
{
  "adjusted_values": {"EBITDA":"string"},
  "rationales": ["Added back lease interest+amortization per ASC 842 ...", "Excluded SBC as non-cash ..."]
}
```

### 5.6 `verify_value`

- **purpose:** Dual‑path verification with tolerance.
- **input:**

```json
{
  "expected":"string",
  "recomputed":"string",
  "tolerance": {"type":"relative|absolute|bp", "value":"0.001"}
}
```

- **output:** `{ "pass": true, "diff": "string" }`

### 5.7 `format_final_answer`

- **purpose:** Enforce final schema.
- **input:**

```json
{
  "question_id": "string",
  "final_answer": {"type":"number|string", "value":"string", "units":"USD|percent|ratio|text"},
  "assumptions": ["..."],
  "justification_bullets": ["...","..."],
  "sources": ["https://..."],
  "calc_trace": [{"op":"...","args":["..."],"result":"..."}]
}
```

- **output:** same object, validated.

---

## 6) Finance Math Engine

### 6.1 Implementation Notes

- Python `decimal.Decimal`; set global context precision (e.g., 34) and `ROUND_HALF_EVEN`.
- Formula registry: `metric_id -> callable(inputs, period) -> Decimal`.
- All inputs/outputs as strings parseable to Decimal.
- **Never** compute inside LLM; LLM only selects formulas and rules.

### 6.2 Core Metric Coverage (v5)

- Profitability & margins: `GROSS_MARGIN`, `OPERATING_MARGIN`, `NET_MARGIN`, `EBITDA`, `EBITDA_MARGIN`, `EBIT`, `FCF_MARGIN`.
- Growth: `YOY_REVENUE_GROWTH`, `QOQ_REVENUE_GROWTH`, `CAGR` (bounded by period availability).
- Cash flow & leverage: `FCF`, `NET_DEBT`, `DEBT_TO_EBITDA`, `INTEREST_COVERAGE`.
- Liquidity: `CURRENT_RATIO`, `QUICK_RATIO`, `WORKING_CAPITAL`.
- Efficiency: `DSO`, `DPO`, `DIO`, `CCC`.
- Per‑share: `EPS_DILUTED`, `SHARES_DILUTED_WA` (as available).

### 6.3 Unit Normalization

- Detect headers: “(in millions)”, “(in thousands)”, “%”.
- Canonical base: USD absolute; percentages as Decimal in **percent units** (e.g., `12.34` means 12.34%).
- For ratios, keep raw Decimal (no percent conversion).

### 6.4 Tolerance Policy

- Currency answers: absolute tolerance **\$0.01**.
- Percent answers: relative tol **0.001** (0.1%) or **10 bp** when expressed in bp.
- Ratios: absolute tol **0.01**.
- Growth rates: relative tol **0.0015**.
- Per‑metric overrides stored in `eval/tolerance_policies.json`.

### 6.5 Dual‑Path Verification

- Path A: direct line item (if exists).
- Path B: recompute from components.
- Accept if within tolerance; else return `verification_failure` and request another assumption/path.

---

## 7) Assumption Rule‑Packs

> Encoded, toggleable adjustments. LLM chooses **which** to apply; tools do the math.

| Key                     | Description                                       | Effect                                            |
| ----------------------- | ------------------------------------------------- | ------------------------------------------------- |
| `ASC842_ADD_BACK`       | Pre‑ASC 842 EBITDA comparability                  | EBITDA += Operating lease interest + amortization |
| `EXCLUDE_SBC`           | Treat SBC as non‑cash, exclude from adjusted OPEX | Adjusted margins increase; subtract SBC from OPEX |
| `EXCLUDE_RESTRUCTURING` | Exclude one‑offs                                  | Add back restructuring costs                      |
| `EXCLUDE_IMPAIRMENT`    | Exclude impairment                                | Add back impairment to operating income           |
| `USE_DILUTED_SHARES`    | Use diluted WA shares for per‑share               | EPS uses diluted, not basic                       |
| `TTM_FROM_LAST_4Q`      | Compute TTM from last 4 quarters                  | Sum Q values; map fiscal quarters                 |
| `CALENDARIZE_FY`        | Align FY to calendar where needed                 | Interpolate/label periods                         |

**Selection prompt hint (for LLM):** Only select rules **explicitly implied** by question or benchmark rubric; otherwise default to GAAP reported values.

---

## 8) Router (Question Classifier)

### 8.1 Classes

- `NARRATIVE` – plain language lookup/definition/explanation.
- `STRUCTURED` – direct line item / table lookup.
- `CALC` – computation required, no special assumptions.
- `ASSUMPTION_CALC` – computation with accounting adjustments.

### 8.2 Features

- Keyword n‑grams ("margin", "growth", "TTM", "adjusted", "exclude", "GAAP", "ASC 842", "diluted").
- Presence of operators (%, increase/decrease, change vs prior).
- Mentions of per‑share, TTM, adjusted/normalized, one‑off.

### 8.3 Implementation

- Start with logistic regression/XGBoost using labelled heuristics from training split.
- Fallback: heuristic rules if router score < threshold.

---

## 9) Filings & Aliases

### 9.1 EDGAR Cache

- Pre‑download/ship HTML/text for dataset `file_link` items into `/data/edgar_cache`.
- Parser pulls tables; store normalized key/values with unit hints.

### 9.2 Alias Map

- Map common synonyms: e.g., `OPERATING_INCOME` ↔ `Operating profit`, `Income from operations`.
- Maintain `aliases.py` with regexes and canonical ids.

---

## 10) Prompts (LLM)

### 10.1 System Prompt (orchestrator)

> You are a finance QA agent. **Never** perform arithmetic yourself. Use the provided tools to fetch filings, normalize units, compute values, apply assumptions, verify results, and format the final answer. Prefer the smallest number of tool calls necessary. If verification fails, try an alternate assumption or formula. Output only via `format_final_answer`.

### 10.2 Tool‑Use Style

- First call `resolve_alias` when a metric is implied.
- Fetch necessary inputs via `fetch_filing_table`.
- Call `normalize_units` for each input before `compute_formula`.
- If question implies adjustments, call `apply_assumptions` with explicit keys.
- Always call `verify_value` before finalization.
- Conclude with `format_final_answer` exactly once.

### 10.3 Few‑Shot Skeletons

- **Margin example**: operating margin FY2023 → alias → fetch REVENUE & OPERATING\_INCOME → normalize → compute → verify (if direct item exists) → format.
- **TTM growth**: revenue TTM vs prior year quarter → fetch 4 quarters → sum → growth → format.
- **Adjusted EBITDA**: select `ASC842_ADD_BACK` + `EXCLUDE_SBC` if prompt says “pre‑ASC 842 adjusted, excluding SBC”.

---

## 11) Output Schema (final)

```json
{
  "question_id": "string",
  "final_answer": {"type":"number|string", "value":"string", "units":"USD|percent|ratio|text"},
  "assumptions": ["ASC842_ADD_BACK"],
  "justification_bullets": [
    "Computed operating margin = operating income / revenue",
    "Units normalized from (in millions) to USD",
    "Verification matched within 6 bp"
  ],
  "sources": ["<dataset file_link>"] ,
  "calc_trace": [
    {"op":"LOOKUP","args":["OPERATING_INCOME"],"result":"..."},
    {"op":"DIVIDE","args":["OPERATING_INCOME","REVENUE"],"result":"..."}
  ]
}
```

---

## 12) Evaluation & Grading

### 12.1 Splits

- Fix a stratified **dev/test** split (80/20) by type: NARRATIVE/STRUCTURED/CALC/ASSUMPTION.
- K‑fold (k=5) for dev.

### 12.2 Tolerance Map

- Store per‑metric policy in `eval/tolerance_policies.json`.
- Grader applies numeric compare with appropriate tolerance; textual questions graded by exact/substring or regex per rubric.

### 12.3 Reports

- Overall accuracy + per‑type.
- Confusion matrix of router.
- Top 20 failures with traces and applied assumptions.

### 12.4 Acceptance Criteria

- Meets KPIs in §1.
- No JSON schema violations across the entire test set.

---

## 13) Non‑Functional Requirements

- **Determinism:** same inputs → same outputs (seeded, stable parser).
- **Observability:** structured logs for every tool call (+ duration, tokens).
- **Speed:** < 3s p95 per question on cached data.
- **Cost:** see KPI ceiling.

---

## 14) Security & Compliance

- No external network calls at runtime (beyond cached filings).
- Inputs/outputs stored locally for reproducibility.
- Sanitize/escape HTML from filings.

---

## 15) Implementation Checklist

-

---

## 16) Milestones

- **M1 (Day 1–2):** Math engine + units + aliases + basic formulas.
- **M2 (Day 3–4):** Assumption rule‑packs + verifier + formatter.
- **M3 (Day 5):** Filings cache parser + router v1.
- **M4 (Day 6):** Eval harness + tolerance policy + reporting.
- **M5 (Day 7):** Prompt polish, failure triage, reach KPI.

---

## 17) Risks & Mitigations

- **Ambiguous prompts → wrong assumptions.** Mitigate with conservative default + require explicit language for adjustments.
- **Table parsing errors.** Keep manual overrides for a few tricky issuers; log low‑confidence extraction.
- **Router misroutes.** Add backoff rule: if `CALC` fails verification, retry as `ASSUMPTION_CALC` with minimal rule.

---

## 18) Example End‑to‑End Traces (abridged)

### 18.1 Operating Margin (FY2023)

1. `resolve_alias("operating margin")` → `OPERATING_MARGIN` requires `OPERATING_INCOME`, `REVENUE`.
2. `fetch_filing_table` → values, units `USD_millions`.
3. `normalize_units` on both.
4. `compute_formula` (OI/REV → percent).
5. `verify_value` vs direct table value.
6. `format_final_answer`.

### 18.2 Adjusted EBITDA (pre‑ASC 842, excl. SBC)

1. Alias `EBITDA`.
2. Fetch OI, D&A, lease interest/amort, SBC.
3. Normalize units.
4. `compute_formula` base EBITDA.
5. `apply_assumptions` with `[ASC842_ADD_BACK, EXCLUDE_SBC]`.
6. Verify (if available).
7. Format final.

---

## 19) Configs

`configs/model.yaml`

```yaml
model: gpt-4o-mini
temperature: 0.1
max_tokens: 1500
function_call: auto
retry: 1
```

`eval/tolerance_policies.json` (sample)

```json
{
  "DEFAULT": {"type":"relative", "value":"0.001"},
  "CURRENCY": {"type":"absolute", "value":"0.01"},
  "PERCENT": {"type":"bp", "value":"10"},
  "RATIO": {"type":"absolute", "value":"0.01"}
}
```

---

## 20) Deliverables

- Working agent (CLI): `python -m scripts.run_eval --model gpt-4o-mini --cache data/edgar_cache`
- Eval report (CSV + HTML) with per‑type metrics and top failures.
- README with quickstart and examples.

---

## 21) Future (post‑v5)

- Fine‑tune orchestrator on schema adherence and rule selection.
- Add more rule‑packs (FX normalization, segment consolidation).
- Integrate a light symbolic planner for complex multi‑step derivations.
- Swap in local 14B model for router and narratives to reduce cost further.

