# FinanceQA Agent Documentation

## Start Here 👋

Welcome! This is a financial Q&A agent that answers questions about company 10-K filings with 90% accuracy. 

**Quick Demo:**
```bash
Q: "What was Costco's revenue in 2024?"
A: "Costco's total revenue in 2024 was $254,123 million.
    {"answer": 254123, "unit": "millions of USD"}"
```

## How It Works 🎯

Instead of one tool trying to do everything, we built three specialized tools:

1. **📊 Financial Metrics Tool** - For questions like "What was the revenue?"
   - Uses: SQLite database with all financial numbers
   - Speed: <100ms
   - Accuracy: 95%+

2. **📚 Document Search Tool** - For questions like "What are the main risks?"
   - Uses: FAISS vectorstore of narrative text
   - Speed: ~200ms  
   - Accuracy: 85%+

3. **🧮 Calculator Tool** - For questions like "Calculate the growth rate"
   - Uses: Safe AST-based math evaluation
   - Speed: <50ms
   - Accuracy: 90%+

A smart router looks at your question and picks the right tool. It's that simple!

## Getting Started 🚀

### 1. Set Up Your Environment
```bash
# Clone the repo
git clone <your-repo>
cd financeAgent

# Install dependencies
pip install -r requirements.txt

# Add your OpenAI key
echo "OPENAI_API_KEY=your-key-here" > .env
```

### 2. Prepare the Data
```bash
# Create the financial database
cd data/
python create_financial_db.py

# Build the narrative search index
cd ../agent/
modal run setup_narrative_kb.py
```

### 3. Deploy the Agent
```bash
# Install Modal (for serverless deployment)
pip install modal
modal setup

# Deploy
modal deploy agent/main_v4.py
```

### 4. Ask Questions!
```bash
# Financial metrics
modal run agent/main_v4.py --question "What was the gross profit margin?"

# Narrative questions  
modal run agent/main_v4.py --question "What are Costco's competitive advantages?"

# Calculations
modal run agent/main_v4.py --question "Calculate 15% of 254 billion"
```

## Understanding the Architecture 🏗️

### The Journey (Why Three Tools?)

We started with one approach: dump the entire 10-K into GPT-4. Results:
- ❌ 46% accuracy
- ❌ $0.55 per question
- ❌ 15 seconds per answer

Then we realized: **financial questions aren't all the same!**

- "What was revenue?" → Just look it up in a table
- "What are the risks?" → Read and understand prose
- "Calculate X" → Do math, don't search

So we built specialized tools for each type. Results:
- ✅ 90% accuracy  
- ✅ $0.02 per question
- ✅ 1-3 seconds per answer

### How Questions Flow

```
Your Question
     ↓
Router Agent ("What type of question is this?")
     ↓
Pick the Right Tool
     ↓
Get the Answer
     ↓
Format Nicely (JSON for numbers)
```

### Key Design Decisions

1. **Why Separate Tools?**
   - Tried: One retrieval system for everything
   - Problem: Poor accuracy, slow, expensive
   - Solution: Specialized tools = better results

2. **Why JSON Output?**
   - Tried: Natural language only
   - Problem: "254 billion" vs "$254B" vs "254,000 million"
   - Solution: `{"answer": 254000, "unit": "millions"}`

3. **Why AST for Calculator?**
   - Tried: `eval()` (simple but dangerous)
   - Problem: Security risk
   - Solution: Parse expressions safely with AST

4. **Why "Think Step-by-Step"?**
   - Tried: Direct prompting
   - Problem: LLMs make silly mistakes
   - Solution: Force reasoning process

## For Developers 🛠️

### Project Structure
```
financeAgent/
├── agent/
│   ├── main_v4.py              # The three-tool agent
│   ├── setup_narrative_kb.py   # Build search index
│   └── (older versions)
├── data/
│   ├── create_financial_db.py  # Build SQL database
│   ├── costco_narrative.txt    # Text sections
│   └── costco_financial_data.db # Numbers database
├── test/
│   ├── evaluate_v4.py          # Accuracy testing
│   └── test_calculator_simple.py # Calculator tests
└── docs/
    ├── README.md               # You are here!
    └── PRD_STORY.md           # The full journey
```

### Adding New Features

**New Financial Metric?**
```python
# Add to data/create_financial_db.py
("Debt to Equity", 2024, 0.85, "ratio"),
```

**New Math Function?**
```python
# Add to agent/main_v4.py calculator
allowed_functions['std'] = statistics.stdev
```

**New Document?**
```bash
# Add to narrative text and rebuild
modal run setup_narrative_kb.py
```

### Testing
```bash
# Run full evaluation
modal run test/evaluate_v4.py

# Test specific tools
modal run test/evaluate_v4.py --test_routing true

# Test calculator locally
python test/test_calculator_simple.py
```

## Common Issues & Solutions 🔧

**"No data found"**
- Check: Is the financial database created?
- Fix: `python data/create_financial_db.py`

**"Could not open narrative_kb_index"**
- Check: Is the FAISS index built?
- Fix: `modal run agent/setup_narrative_kb.py`

**Wrong tool selected**
- Check: Router agent logs
- Fix: Update router examples in `router_agent_v4()`

**Calculation errors**
- Check: Is the expression valid Python?
- Fix: Test in `test_calculator_simple.py`

## Future Roadmap 🚀

### Coming Soon (2 weeks)
- **Assumptions**: Handle missing data intelligently
- **Multi-step**: "Calculate X, then use it for Y"
- **Confidence**: Know when we might be wrong

### Next Quarter
- **Real-time data**: Market prices, news
- **Comparisons**: "How does Costco compare to Walmart?"
- **Trends**: "Show revenue growth over 5 years"

### Long Term Vision
- **Financial Advisor**: Investment recommendations
- **Multi-language**: Support global markets
- **Voice Interface**: "Alexa, what's Apple's P/E ratio?"

## The Philosophy 💭

Good software understands its domain. Great software embraces it.

We didn't build a generic Q&A system that happens to work on financial data. We built a financial analyst that happens to be software.

Every decision—from three specialized tools to structured JSON output—came from understanding how financial analysis actually works.

**Remember**: The best solution isn't always the most sophisticated. Sometimes it's the one that deeply understands the problem.

---

*For the full story of how we went from 46% to 90% accuracy, check out [PRD_STORY.md](PRD_STORY.md)*
