import modal
from datasets import load_dataset
import os

# Define the Modal app with required dependencies
app = modal.App(
    "finance-evaluate",
    image=modal.Image.debian_slim().pip_install("datasets"),
    # Optional: Include HF token secret if needed for private datasets
    secrets=[modal.Secret.from_name("hf-token")] if "HF_TOKEN" in os.environ else []
)

# Evaluation function
@app.function()
def evaluate_agent():
    # Load the FinanceQA test set (public dataset, no login required)
    dataset = load_dataset("AfterQuery/FinanceQA", split="test")

    # Get the process_question function from the agent app
    process_question = modal.Function.lookup("finance-agent", "process_question")

    correct = 0
    total = len(dataset)
    for row in dataset:
        result = process_question.remote(row["question"], row["context"])
        if result == row["answer"]:
            correct += 1
    accuracy = (correct / total) * 100
    print(f"Accuracy: {accuracy}%")

# Local entrypoint to trigger evaluation
@app.local_entrypoint()
def main():
    evaluate_agent.remote()