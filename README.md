# FinanceQA Agent

This is a Python-based agent for the FinanceQA benchmark, running on Modal with OpenAI's GPT-4o. It tackles financial analysis questions (tactical and conceptual) to achieve >60% accuracy.

## Setup

### Install Modal CLI

```bash
pip install modal
modal setup
```

### Set Secrets

**OpenAI API Key:**
```bash
modal secret create openai-key-1 OPENAI_API_KEY=your-openai-api-key
```

**Hugging Face Token (optional, for private datasets):**
```bash
modal secret create hf-token HF_TOKEN=your-huggingface-token
```

### Clone Repo
```bash
git clone your-repo-url
cd your-repo-folder
```

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

## Files

- `agent.py`: Core agent logic.
- `evaluate.py`: Evaluates against FinanceQA test set.
- `requirements.txt`: Lists dependencies (openai, datasets, modal).
- `README.md`: This file.

## Troubleshooting

- **Modal Issues**: Check dashboard logs for errors.
- **Low Accuracy**: Add more examples to agent.py prompts.
- **Dataset Access**: FinanceQA is public, no login needed. For private datasets, use hf-token.

