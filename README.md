# FinanceQA Agent

An AI agent for financial document analysis, achieving **46.7% accuracy** on the FinanceQA benchmark through intelligent document retrieval and multi-step reasoning.

## Agent Card

| Property | Value |
|----------|-------|
| **Task** | Financial Q&A from 10-K documents |
| **Model** | GPT-4o with FAISS retrieval |
| **Accuracy** | 46.7% (approaching 56.8% baseline) |
| **Token Usage** | ~2,000 per query (96% reduction) |
| **Response Time** | 2-3 seconds |
| **Cost** | ~$0.02 per query |

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

### Option 1: Modal (Recommended for Production)

Modal provides serverless GPU compute and automatic scaling.

#### 1. Install Modal
```bash
pip install modal
modal setup  # Authenticate (one-time)
```

#### 2. Set Secrets
```bash
modal secret create openai-key-1 OPENAI_API_KEY=your-key-here
```

#### 3. Deploy
```bash
modal deploy agent/main.py
```

#### 4. Run
```bash
# Test a single question
modal run agent/main.py --question "What was Costco's revenue in 2024?"

# Run 20-question test suite
modal run test/quick_test.py
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

## Project Structure

```
financeAgent/
├── README.md              # This file
├── requirements.txt       # Dependencies
├── .env                  # API keys (create this)
│
├── agent/                # Core agent code
│   ├── main.py          # 🎯 Main agent to deploy/run
│   └── setup_knowledge_base.py
│
├── test/                 # Test suites
│   ├── quick_test.py    # 🎯 20-question test
│   └── evaluate.py      # Full benchmark
│
├── data/                 # Financial documents
│   ├── costco_10k_full.txt     # Complete 10-K (218KB)
│   └── costco_10k_summary.txt  # Brief summary (1.6KB)
│
├── docs/                 # Documentation
└── dump/                 # Results & logs
```

## Features

- **Intelligent Retrieval**: FAISS vector search finds relevant document sections
- **Token Optimization**: Reduces context from 55k to 2k tokens
- **Multi-Agent Architecture**: Router, retrieval, and answer agents
- **Cost Effective**: 96% reduction in API costs
- **Production Ready**: Deployed on Modal with automatic scaling

## Performance

On the FinanceQA benchmark:
- **Basic Tactical**: ~65% accuracy
- **Conceptual**: ~60% accuracy
- **Overall**: 46.7% accuracy

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

