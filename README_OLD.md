# FinanceQA Agent v4

A specialized AI agent that answers financial questions with 90% accuracy by using the right tool for each job.

## What Makes It Special 🎯

Instead of one tool trying to do everything, we built three specialized tools:
- **📊 SQL Database** for financial metrics ("What was the revenue?")
- **📚 Document Search** for narrative content ("What are the risks?")  
- **🧮 Safe Calculator** for computations ("Calculate the growth rate")

Result: 90% accuracy vs 46% for the "dump everything into GPT" approach.

## Quick Start

### Prerequisites

```bash
# Python 3.9+
python --version

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file:
```bash
OPENAI_API_KEY=your-openai-key-here
```

## Deployment Options

### Option 1: Modal v4 Deployment (Recommended)

Modal provides serverless compute with automatic scaling.

#### 1. Setup Data Sources
```bash
# Create financial database
cd data/
python create_financial_db.py

# Build narrative vectorstore
cd ../agent/
modal run setup_narrative_kb.py
```

#### 2. Install Modal
```bash
pip install modal
modal setup  # Authenticate (one-time)
```

#### 3. Set Secrets
```bash
modal secret create openai-key-1 OPENAI_API_KEY=your-key-here
```

#### 4. Deploy v4 Agent
```bash
modal deploy agent/main_v4.py
```

#### 5. Test the Three Tools
```bash
# Test structured data lookup
modal run agent/main_v4.py --question "What was Costco's revenue in 2024?"

# Test narrative search
modal run agent/main_v4.py --question "What are Costco's main risk factors?"

# Test calculator
modal run agent/main_v4.py --question "Calculate 15% of 254 billion"
```

### Option 2: Local Development

For testing without Modal deployment:

```bash
# Load environment
source load_env.sh

# Run locally
python agent/agent_v3_enhanced.py \
  --question "What was Costco's revenue in 2024?"
```

## Project Structure (v4)

```
financeAgent/
├── README.md                    # This file
├── requirements.txt             # Dependencies
├── .env                        # API keys (create this)
│
├── agent/                      # Core agent code
│   ├── main_v4.py             # 🎯 v4 Three-tool agent
│   ├── main.py                # v3 agent (previous)
│   ├── setup_narrative_kb.py  # Build narrative FAISS
│   └── setup_knowledge_base.py # Original KB builder
│
├── test/                       # Test suites
│   ├── evaluate_v4.py         # 🎯 v4 evaluation
│   ├── test_calculator_simple.py # Calculator tests
│   └── evaluate.py            # v3 evaluation
│
├── data/                       # Financial data
│   ├── costco_financial_data.db # SQLite database
│   ├── costco_narrative.txt    # Narrative text
│   ├── create_financial_db.py  # DB creation script
│   └── costco_10k_full.txt    # Original 10-K
│
├── docs/                       # Documentation
│   ├── CURRENT_VERSION_V4.md  # v4 release notes
│   ├── V4_ARCHITECTURE.md     # Architecture details
│   └── V4_MIGRATION_GUIDE.md  # Migration guide
│
└── dump/                       # Results & logs
```

## v4 Features

### Three Specialized Tools
1. **Structured Data Lookup**: SQLite queries for financial metrics
2. **Document Search**: FAISS retrieval for narrative content only  
3. **Python Calculator**: AST-based safe mathematical evaluation

### Key Improvements
- **Smart Routing**: Automatically selects the best tool
- **Structured Output**: JSON format for numerical answers
- **Token Optimization**: <500 tokens for structured queries
- **Enhanced Prompts**: "Think step-by-step" reasoning
- **Better Accuracy**: 90%+ on financial metrics

## Performance (v4)

### By Question Type
- **Financial Metrics**: ~95% accuracy (from SQLite)
- **Calculations**: ~90% accuracy (AST calculator)
- **Narrative/Conceptual**: ~85% accuracy (focused FAISS)
- **Overall**: 85-90% accuracy

### Efficiency
- **Response Time**: 1-3 seconds
- **Token Usage**: Optimized per tool type
- **Cost**: $0.01-0.02 per query

## Troubleshooting

### Modal Issues

**Authentication Error**
```bash
modal setup  # Re-authenticate
```

**Deployment Failed**
```bash
# Check Modal dashboard
modal app list
# Redeploy
modal deploy agent/agent_v3_enhanced.py --force
```

**Secret Not Found**
```bash
modal secret list
modal secret create openai-key-1 OPENAI_API_KEY=your-key
```

### Local Issues

**Module Not Found**
```bash
pip install -r requirements.txt
```

**API Key Error**
```bash
# Check .env file
cat .env
# Reload environment
source load_env.sh
```

## License

MIT

## Contact

For issues or questions, please open a GitHub issue

