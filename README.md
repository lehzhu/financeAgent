# FinanceQA Agent

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

## How It Meets the PRD

- **>60% Accuracy**: Uses GPT-4o with few-shot prompts to surpass the 56.8% baseline, especially on assumption-based questions.
- **Handles All Questions**: Processes tactical (context-based) and conceptual (reasoning-based) questions for any company.
- **Fast Development**: Built in <4 hours, deployable on Modal.
- **Submission-Ready**: Includes agent.py, evaluate.py, requirements.txt, and this README.

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

- `agent.py`: Main agent with GPT-4o integration
- `evaluate.py`: Evaluation script for FinanceQA dataset
- `test_agent.py`: Test version without API calls
- `test_evaluate.py`: Quick evaluation test (3 samples)
- `requirements.txt`: Python dependencies
- `.env`: API keys (create from .env.example)
- `load_env.sh`: Environment loader script
- `sync-to-github.sh`: Auto-sync to GitHub

## Troubleshooting

- **OpenAI API Errors**: Check quota at https://platform.openai.com/account/billing
- **Rate Limits**: Script includes retry logic with 60-second pause
- **Module Import Errors**: Both apps need `openai` in Modal image
- **Environment Variables**: Use `source load_env.sh` before running
- **modal run vs deploy**: Use `run` for testing, `deploy` for production

