# FinanceQA Evaluation Report

Generated: 2025-08-09 10:59:43

Dataset: FinanceQA 10-sample (focused retrieval v2)


## Summary by question_type

type | n | EM | EM% | F1 avg | span% | numeric% | verify dist
--- | ---: | ---: | ---: | ---: | ---: | ---: | ---
basic | 3 | 0 | 0.0% | 0.111 | 0.0% | 0.0% | -
assumption | 4 | 0 | 0.0% | 0.000 | 0.0% | 0.0% | insufficient:4
conceptual | 3 | 0 | 0.0% | 0.000 | - | 0.0% | -

## Detailed results

### assumption

- id: row_2
  question: What is adjusted EBITDA for the year ending in 2024?
  gold: $11,969 (in millions)
  pred: 
  metrics: EM=0, F1=0.000, span=False, numeric_close=False, verify=insufficient

- id: row_3
  question: What is adjusted EBIT for the year ending in 2024?
  gold: $9,396 (in millions)
  pred: 
  metrics: EM=0, F1=0.000, span=False, numeric_close=False, verify=insufficient

- id: row_6
  question: Compute the adjusted EBITDA Margin for 2024.
  gold: 4.70%
  pred: 
  metrics: EM=0, F1=0.000, span=False, numeric_close=False, verify=insufficient

- id: row_9
  question: Determine the EV/EBITDA ratio for 2024. Make sure to adjust for EBITDA and use the market value of equity to estimate enterprise value. Make sure to hand calculated fully diluted shares outstanding. Assume the only non-operating asset is excess cash.
  gold: 35.44x
  pred: 
  metrics: EM=0, F1=0.000, span=False, numeric_close=False, verify=insufficient

### basic

- id: row_0
  question: What is Gross Profit in the year ending 2024?
  gold: $32,095 (in millions)
  pred: Not supported by the filing
  metrics: EM=0, F1=0.000, span=False, numeric_close=False, verify=None

- id: row_1
  question: What is unadjusted EBITDA for the year ending in 2024?
  gold: $11,522 (in millions)
  pred: Not supported by the filing
  metrics: EM=0, F1=0.000, span=False, numeric_close=False, verify=None

- id: row_7
  question: What is unadjusted EBIT for the year ending in 2024?
  gold: $9,285 (in millions)
  pred: $9,740
  metrics: EM=0, F1=0.333, span=False, numeric_close=False, verify=None

### conceptual

- id: row_4
  question: Company X trades at $15 per share and has 80 shares outstanding, with $80 in net income. Company Y trades at $30 per share, has 15 shares outstanding, and earns $20 in net income. Company X acquires Company Y at no premium, paying 60% in new stock and 40% in cash. After the transaction, what is the percentage change in Company X's EPS?
  gold: 2%
  pred: 
  metrics: EM=0, F1=0.000, span=None, numeric_close=False, verify=None

- id: row_5
  question: You deposit $80 right now. After three years, your annual IRR is 10%. How much will your deposit be worth at the end of those three years?
  gold: $106.48
  pred: 
  metrics: EM=0, F1=0.000, span=None, numeric_close=False, verify=None

- id: row_8
  question: Let's say you're going to receive $75 in 7 years, with a discount rate of 9%. What is its value today?
  gold: $41.06
  pred: 
  metrics: EM=0, F1=0.000, span=None, numeric_close=False, verify=None
