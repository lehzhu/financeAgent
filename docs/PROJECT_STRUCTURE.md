# Project Structure

## Overview

The FinanceQA Agent project is organized into clear, logical folders for maintainability and clarity.

## Directory Layout

```
financeAgent/
│
├── agent/                    # Core agent implementations
│   ├── agent_v3_enhanced.py # Main production agent (FAISS + smart filtering)
│   ├── agent_v3_fullcontext.py # Simple full-context approach
│   ├── agent_v2_final.py    # Previous FAISS version
│   ├── agent_v2.py          # Earlier iteration
│   ├── agent.py             # Original implementation
│   ├── build_kb.py          # Knowledge base builder
│   └── build_knowledge_base.py # Alternative KB builder
│
├── test/                    # Test suites and debugging
│   ├── evaluate.py          # Main evaluation script
│   ├── test_v3_local.py    # Local testing without Modal
│   ├── test_parallel_v2.py # Parallel evaluation
│   ├── test_sequential_v2.py # Sequential evaluation
│   ├── test_v3_fullcontext.py # Full context testing
│   └── debug_*.py          # Various debugging scripts
│
├── docs/                    # Documentation
│   ├── PRD.md              # Product requirements & roadmap
│   ├── CURRENT_VERSION.md  # v3 release notes
│   ├── MODAL_DEPLOYMENT.md # Modal deployment guide
│   └── PROJECT_STRUCTURE.md # This file
│
├── data/                    # Financial documents
│   ├── costco10k.txt       # Costco 10-K filing
│   ├── cost-20240901.html  # HTML version
│   └── parse_html.py       # HTML parser utility
│
├── dump/                    # Logs, results, experiments
│   ├── evaluation_results.md # Performance metrics
│   ├── v2_agentic_results.md # v2 test results
│   ├── context_window_analysis.md # Token usage analysis
│   └── *.py                # Experimental scripts
│
├── zeroentropy/            # Optional ZeroEntropy integration (gitignored)
│   └── [Experimental features]
│
└── [Root Files]
    ├── README.md           # Main documentation
    ├── requirements.txt    # Python dependencies
    ├── .env               # API keys (gitignored)
    ├── .gitignore         # Git exclusions
    ├── load_env.sh        # Environment loader
    └── activate.sh        # Virtual env activation
```

## Key Files

### Production Agent
- **`agent/agent_v3_enhanced.py`** - The main agent to deploy

### Testing
- **`test/evaluate.py`** - Run full FinanceQA benchmark
- **`test/test_v3_local.py`** - Test locally without Modal

### Documentation
- **`README.md`** - User-facing documentation
- **`docs/PRD.md`** - Product requirements and roadmap
- **`docs/CURRENT_VERSION.md`** - v3 features and changes

### Configuration
- **`.env`** - API keys (create from template)
- **`requirements.txt`** - Python dependencies

## Development Workflow

1. **Local Development**: Work in `agent/` folder
2. **Testing**: Use scripts in `test/` folder
3. **Documentation**: Update files in `docs/`
4. **Results**: Store outputs in `dump/`
5. **Data**: Keep documents in `data/`

## Deployment

```bash
# Deploy the main agent
modal deploy agent/agent_v3_enhanced.py

# Run evaluation
modal run test/evaluate.py

# Test locally
python test/test_v3_local.py
```

## Clean Code Principles

- No files in root except essential configs
- Clear folder names indicating purpose
- Experimental features isolated (zeroentropy/)
- Logs and results separated (dump/)
- Documentation centralized (docs/)

This structure ensures the project remains maintainable and professional as it grows.
