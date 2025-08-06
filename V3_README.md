# Finance Agent v3 - Enhanced with Smart Retrieval

## What's New in v3

This branch combines the best features from v2 (FAISS) and adds smart filtering with optional ZeroEntropy support:

- **96% token reduction**: From 55k to ~2k tokens per query
- **Smart retrieval**: FAISS gets 20 chunks, filters to top 5
- **Optional ZeroEntropy**: Can enhance with AI reranking when needed
- **Clean project structure**: Organized into proper folders

## Project Structure

```
financeAgent/
├── agent_v3_enhanced.py      # Main enhanced agent with FAISS + smart filtering
├── agent_v3_fullcontext.py   # Simple full-context approach
├── agent_v2_final.py         # Previous v2 with basic FAISS
├── setup_ze_collection.py    # Optional ZeroEntropy setup
│
├── data/                     # Costco financial data
│   ├── costco10k.txt
│   └── cost-20240901.html
│
├── tests/                    # All test files
│   ├── test_v3_local.py     # Local testing
│   ├── test_parallel_v2.py  # Parallel evaluation
│   └── debug_*.py           # Debug scripts
│
├── docs/                     # Documentation
│   └── zeroentropy/         # ZeroEntropy integration docs
│       ├── V3_ENHANCED_README.md
│       └── ZEROENTROPY_DEBUG_SUMMARY.md
│
└── dump/                     # Logs, results, experiments
    ├── evaluation_results.md
    └── zeroentropy_demo.py
```

## Quick Start

### 1. Deploy the Enhanced Agent

```bash
modal deploy agent_v3_enhanced.py
```

### 2. Test a Query

```bash
modal run agent_v3_enhanced.py --question "What was Costco's revenue in 2024?"
```

### 3. Compare Retrieval Methods

```bash
modal run agent_v3_enhanced.py --compare true
```

## How It Works

1. **FAISS Retrieval**: Finds 20 semantically similar chunks
2. **Smart Filtering**: Reduces to top 5 most relevant
3. **LLM Processing**: GPT-4 answers using focused context
4. **Optional ZeroEntropy**: Can enhance with AI reranking if configured

## Performance

- **Token Usage**: ~2,000 tokens (vs 55,000 for full document)
- **Cost**: ~$0.02 per query (vs $0.55)
- **Speed**: 2-3 seconds (vs 10-15 seconds)
- **Accuracy**: Maintained with focused context

## Optional: ZeroEntropy Setup

If you want even better ranking:

```bash
python setup_ze_collection.py
```

This creates a ZeroEntropy collection for enhanced retrieval, but the agent works great with just FAISS.

## Testing

```bash
# Local test without Modal
python tests/test_v3_local.py

# Full evaluation
modal run evaluate.py
```

## Key Files

- `agent_v3_enhanced.py` - The main agent to use
- `setup_ze_collection.py` - Optional ZeroEntropy setup
- `tests/test_v3_local.py` - Local testing script
- `docs/zeroentropy/` - Full documentation

The v3 agent is production-ready and provides excellent performance with or without ZeroEntropy!
