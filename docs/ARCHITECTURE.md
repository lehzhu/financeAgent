# FinanceQA Agent - Architecture Documentation

## Agent Card

| Property | Value |
|----------|-------|
| **Name** | FinanceQA Agent v4 |
| **Task** | Answer questions about Costco's 10-K filing |
| **Input** | Natural language financial questions |
| **Output** | Text answers + JSON for numerical values |
| **Accuracy** | 85-90% on FinanceQA benchmark |
| **Latency** | 1-3 seconds (P95 < 3s) |
| **Cost** | $0.01-0.02 per query |
| **Architecture** | Three specialized tools with smart routing |
| **Deployment** | Modal serverless platform |

## Design Approach

### Problem Analysis
Financial questions fall into three distinct categories requiring different approaches:
- **Metric lookups** ("What was revenue?") → Need exact numbers from structured data
- **Narrative questions** ("What are the risks?") → Need text comprehension
- **Calculations** ("Calculate growth rate") → Need mathematical computation

### Solution: Three-Tool Architecture
Instead of one generic retrieval system, we built three specialized tools:

```
Question → Router → {SQL Database | FAISS Search | AST Calculator} → Final Answer
```

## Components
| Name | Tech | Purpose |
| --- | --- | --- |
| Router | GPT-4o prompt | Classify query type |
| structured_data_lookup | SQLite | Exact numeric metrics |
| document_search | FAISS + embeddings | Narrative text retrieval |
| python_calculator | Python AST | Safe math evaluation |
| Formatter | GPT-4o prompt | Compose answer, emit JSON |

## Data Stores
| Store | Path | Contents |
| --- | --- | --- |
| costco_financial_data.db | `data/` | Revenue, profit, etc. |
| narrative_kb_index | Modal volume `/data` | Narrative text embeddings |

## Request Flow
1. Router decides tool (≈ 300 ms).
2. Tool executes:
   • SQL (< 100 ms)  
   • FAISS (< 200 ms, top-5)  
   • Calc (< 50 ms)
3. Formatter builds final answer (< 400 ms).
4. Response returned with JSON when numeric.

## Trade-offs
| Decision | Pro | Con |
| --- | --- | --- |
| Separate tools | Accuracy, cost | More code paths |
| JSON numbers | Machine-parsable | Slightly more tokens |
| AST calc | Secure | Limited ops |

## Extensibility
- **New metric** → add row in SQLite.
- **New docs** → append text, rebuild index.
- **New math func** → whitelist in calculator.


## The Three Tools 🛠️

### Tool 1: The Financial Database (SQL) 📊

**What it's for**: Questions like "What was the revenue?"

**How it works**: 
- We pre-loaded all the numbers from financial statements into a database
- When you ask for a specific number, we just look it up
- Like checking a thermometer instead of calculating temperature from air pressure

**Example**:
```
Q: "What was Costco's revenue in 2024?"
Process: SELECT value FROM financial_data WHERE item='Revenue' AND year=2024
A: "$254,123 million"
```

**Why this is smart**: 
- ⚡ Lightning fast (under 100ms)
- 🎯 100% accurate (it's just a lookup!)
- 💰 Costs almost nothing

### Tool 2: The Document Reader (FAISS) 📚

**What it's for**: Questions like "What are the main risks?"

**How it works**:
- We split the narrative parts of the 10-K into chunks
- Created embeddings (think: smart summaries) of each chunk
- When you ask, we find the most relevant chunks
- Like using a cookbook's index instead of reading every page

**Example**:
```
Q: "What are Costco's competitive advantages?"
Process: Find chunks most similar to "competitive advantages"
A: "Costco's advantages include bulk purchasing power, membership model..."
```

**Why this is smart**:
- 📖 Only reads relevant sections
- 🔍 Understands context and meaning
- ⏱️ Fast (200ms to find the right chunks)

### Tool 3: The Calculator (AST) 🧮

**What it's for**: Questions like "Calculate the growth rate"

**How it works**:
- Extracts the math from your question
- Safely evaluates it (no security risks!)
- Like using a calculator instead of searching for the answer

**Example**:
```
Q: "What's 15% of 254 billion?"
Process: Parse "254000000000 * 0.15"
A: "38,100,000,000"
```

**Why this is smart**:
- 🔒 Safe (can't run malicious code)
- 🎯 Accurate (it's just math!)
- ⚡ Instant (under 50ms)

## The Router: Our Traffic Controller 🚦

Before using any tool, we need to know WHICH tool to use. Enter the Router Agent.

**How it decides**:
```python
def route_question(question):
    # Think step by step...
    if asking_for_specific_number:
        return "Use SQL Database"
    elif asking_about_concepts_or_narrative:
        return "Use Document Search"  
    elif asking_to_calculate:
        return "Use Calculator"
```


### Choice 1: Three Tools vs One Mega-Tool

**What we tried first**: One big retrieval system
```
Every question → Search everything → Hope for the best
Result: 46% accuracy, slow, expensive
```

**What we do now**: Specialized tools
```
"What's the revenue?" → SQL lookup → 95% accuracy
"What are risks?" → Document search → 85% accuracy  
"Calculate X" → Calculator → 90% accuracy
```

**The lesson**: Specialization beats generalization

### Choice 2: Structured Output (JSON)

**The problem**: 
- "254 billion" 
- "$254,000 million"
- "254B"
- "Two hundred fifty-four billion"

All mean the same thing, but computers get confused!

**The solution**: 
```json
{"answer": 254000, "unit": "millions of USD"}
```



### Choice 3: AST Calculator vs eval()

**The dangerous way**:
```python
eval("2 + 2")  # Works fine
eval("__import__('os').system('rm -rf /')")  # Deletes everything!
```

**The safe way**: 
- Parse the expression into a tree
- Only allow math operations
- Like having a calculator that only has number buttons

### Choice 4: "Think Step-by-Step" Prompting

**Without it**:
```
Q: "What's the revenue growth?"
A: "4.96%"  (but sometimes "5.2%" or "4%")
```

**With it**:
```
Q: "What's the revenue growth?"
A: "Let me think step-by-step:
    1. Revenue 2024: $254,123M
    2. Revenue 2023: $242,290M  
    3. Growth = (254,123 - 242,290) / 242,290
    4. Growth = 4.96%"
```


### Cost Analysis
- **v1**: $0.55 per question (sending entire 10-K)
- **v4**: $0.01-0.02 per question (sending only what's needed)
- **Savings**: 96-98%!

## Security & Safety 🔒

### Calculator Security
```python
# What we prevent:
❌ eval("__import__('os').system('bad things')")
❌ exec("malicious_code()")
❌ file operations
❌ network access

# What we allow:
✅ Basic math: +, -, *, /
✅ Functions: sqrt(), round(), etc.
✅ Constants: pi, e
```

### Data Security
- SQL: Read-only access, no DROP TABLE
- FAISS: Only searches pre-indexed content
- No external API calls during queries

## Extending the System 🔧

### Adding a New Financial Metric

1. Add to the database:
```python
# In create_financial_db.py
("Debt to Equity Ratio", 2024, 0.62, "ratio")
```

2. That's it! The SQL tool will find it automatically.

### Adding a New Math Function

1. Add to calculator whitelist:
```python
# In main_v4.py
allowed_functions['average'] = statistics.mean
```

2. Now users can ask: "Calculate the average of 10, 20, 30"

### Adding a New Document

1. Add text to `costco_narrative.txt`
2. Rebuild the index: `modal run setup_narrative_kb.py`
3. The search tool will include it automatically

