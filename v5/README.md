# FinanceQA Agent – Project Layout

This directory contains the baseline implementation for the v5 agent as outlined in v5/documentation.

Structure
- agent/: Orchestrator, routing, and prompts used to coordinate tools.
- tools/: Deterministic tools (math, assumptions, units, filings access, alias resolution, verification, formatting).
- eval/: Batch evaluation harness and grading utilities.
- configs/: Model and logging configuration.
- scripts/: Helper scripts for running evaluation and exporting reports.
- data/: Dataset files and cached EDGAR tables (if any).

Quick start

Local
1) Create/obtain a FinanceQA dataset file at data/financeqa.json. Each item should include at least: id, question, optional context, and the official answer for evaluation.
2) Run local evaluation:
   python3 eval/evaluate.py --dataset data/financeqa.json --limit 10

Modal (recommended for team use)
1) Ensure Modal is set up (one-time):
   modal token set
2) (Optional for baseline) Create an OpenAI secret in Modal (stores OPENAI_API_KEY securely) for future LLM use:
   modal secret create openai
3) Run v5 evaluation in Modal (writes to a Modal Volume):
   # Local JSON file
   modal run evaluate_v5.py::run_eval --dataset-path data/financeqa.json --limit 10 --out-path /root/results/results.json
   # Hugging Face dataset (recommended)
   modal run evaluate_v5.py::run_eval --dataset-path hf:AfterQuery/FinanceQA --limit 100 --out-path /root/results/results.json
4) Retrieve results (option 1): run again and print path; (option 2) use modal volume CLI to copy out; (option 3) adapt evaluate_v5.py to upload to S3/GCS.

Notes
- The orchestrator is designed to be model-agnostic; plug in your LLM client in agent/orchestrator.py where indicated.
- The Finance Math Engine uses decimal.Decimal for precise arithmetic and returns strict JSON-serializable outputs.
- All tool inputs/outputs avoid floats and instead use strings that parse to Decimal, as required by the PRD.
- Secrets: Never commit keys. For local, export OPENAI_API_KEY in your shell; for Modal, you can create secrets like `modal secret create openai` (OPENAI_API_KEY) and `modal secret create huggingface` (HUGGINGFACE_HUB_TOKEN). The baseline does not require these unless you wire in the LLM or private HF datasets.

