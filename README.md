# FinanceQA Agent

## Performance

- **Accuracy: 46.7%** (with smart matching)
- **Baseline to beat: 56.8%** (from original paper)
- **Detailed results**: See [evaluation_results.md](evaluation_results.md) for a full breakdown

This is a Python-based agent for the FinanceQA benchmark, running on Modal with OpenAI's GPT-4o. It tackles financial analysis questions (tactical and conceptual) to achieve >60% accuracy.

## Setup

### Local Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Set API Keys

**Option 1: Environment File (Recommended)**
```bash
# Create .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env

# Load environment
source load_env.sh
```

**Option 2: Modal Secrets**
```bash
# For Modal deployment
modal secret create openai-key-1 OPENAI_API_KEY=your-api-key
```

### Install Modal

```bash
pip install modal
modal setup  # Authenticate with Modal
```

## Usage

### Deploy Agent
```bash
modal deploy agent.py
```

### Run Evaluation
```bash
modal run evaluate.py
```
Outputs accuracy on the FinanceQA test set.

### Test a Question
```bash
modal run agent.py --question "Calculate NOPAT for 2024." --context "The company's EBIT for 2024 is $1,000, and the effective tax rate is 30%."
```

## Current Results

- **Accuracy**: 46.7% with smart matching (approaching the 56.8% baseline)
- **Handles All Questions**: Successfully processes both tactical (context-based) and conceptual (reasoning-based) questions
- **Fast Response**: ~15 seconds per question on average
- **Production Ready**: Deployed on Modal with automatic rate limiting and error handling

## Future Extensions

### Zeroentropy Reranking
Add tool calls (e.g., fetch 10-Ks from SEC EDGAR) and use a reranking model to select relevant sections, improving context for tactical questions.

### GPT-OSS on Modal GPUs
Run OpenAI's GPT-OSS locally on Modal GPUs to cut API costs and enhance security. Requires loading pretrained weights and GPU optimization.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/lehzhu/financeAgent.git
cd financeAgent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure API key
cp .env.example .env  # Edit with your OpenAI key
source load_env.sh

# Run a test
modal run agent.py --question "Calculate NOPAT" --context "EBIT=$1000, tax=30%"
```

## Files

### Core Files
- `agent.py`: Main agent with GPT-4o integration
- `requirements.txt`: Python dependencies
- `evaluation_results.md`: Latest performance metrics and analysis

### Evaluation Scripts
- `evaluate.py`: Full evaluation (148 questions, ~30 min)
- `evaluate_improved.py`: Evaluation with smart matching and transparency
- `quick_evaluate.py`: Quick evaluation (20 questions, ~10 min)
- `test_evaluate.py`: Minimal test (3 questions)

### Utilities
- `.env`: API keys (create from template)
- `load_env.sh`: Environment loader script
- `sync-to-github.sh`: Auto-sync to GitHub
- `activate.sh`: Virtual environment activation

## Troubleshooting

- **OpenAI API Errors**: Check quota at https://platform.openai.com/account/billing
- **Rate Limits**: Script includes retry logic with 60-second pause
- **Module Import Errors**: Both apps need `openai` in Modal image
- **Environment Variables**: Use `source load_env.sh` before running
- **modal run vs deploy**: Use `run` for testing, `deploy` for production

