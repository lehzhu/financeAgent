# Project Structure

## Core Files You Need to Know

```
financeAgent/
│
├── agent/main_v4.py           ⭐ The main agent (deploy this!)
├── data/create_financial_db.py    📊 Creates the SQL database  
├── agent/setup_narrative_kb.py    📚 Builds the search index
└── test/evaluate_v4.py            ✅ Tests accuracy
```

## Quick Reference

### To Add Features
- **New financial metric?** → Edit `data/create_financial_db.py`
- **New math function?** → Edit calculator in `agent/main_v4.py`  
- **New document?** → Add to `data/costco_narrative.txt` and rebuild

### To Test
- **Test everything:** `modal run test/evaluate_v4.py`
- **Test calculator:** `python test/test_calculator_simple.py`
- **Test one question:** `modal run agent/main_v4.py --question "..."`

### Key Data Files
- `data/costco_financial_data.db` - All the numbers (revenue, profit, etc.)
- `data/costco_narrative.txt` - All the text (risks, strategy, etc.)

## Full Structure

```
financeAgent/
├── README.md                  # Quick start guide
├── requirements.txt           # Python packages needed
├── .env                      # Your OpenAI key (create this)
│
├── agent/                    # The brains
│   ├── main_v4.py           # Current three-tool agent ⭐
│   ├── setup_narrative_kb.py # Builds FAISS search index
│   └── archive/             # Old versions (ignore)
│
├── data/                     # The knowledge  
│   ├── create_financial_db.py    # Script to build SQL database
│   ├── costco_financial_data.db  # SQLite with all metrics
│   ├── costco_narrative.txt      # Text from 10-K filing
│   └── costco_10k_full.txt       # Original document
│
├── test/                     # Quality checks
│   ├── evaluate_v4.py       # Full accuracy test
│   ├── test_calculator_simple.py # Calculator unit tests
│   └── benchmark_real.py    # Real-world questions
│
├── docs/                     # How it all works
│   ├── README.md           # Complete user guide  
│   ├── ARCHITECTURE.md     # Technical deep dive
│   └── PRD.md             # The journey from 46% to 90%
│
└── dump/                     # Logs and experiments
    └── (various test results and experiments)
```

## Workflow

1. **Setup**: Run database and index builders
2. **Deploy**: `modal deploy agent/main_v4.py`
3. **Test**: Run evaluation scripts
4. **Iterate**: Add features, rebuild, test again

That's it! The beauty is in the simplicity. 🎯
