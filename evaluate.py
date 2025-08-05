import modal
from datasets import load_dataset
import os
import time

# Define the Modal app with required dependencies
app = modal.App(
    "finance-evaluate",
    image=modal.Image.debian_slim().pip_install("datasets", "openai"),
    # Optional: Include HF token secret if needed for private datasets
    secrets=[modal.Secret.from_name("hf-token")] if "HF_TOKEN" in os.environ else []
)

# Evaluation function
@app.function(timeout=600)
def evaluate_agent():
    # Load the FinanceQA test set (public dataset, no login required)
    dataset = load_dataset("AfterQuery/FinanceQA", split="test")

    # Get the process_question function from the agent app
    process_question = modal.Function.from_name("finance-agent", "process_question")

    correct = 0
    total = len(dataset)
    for i, row in enumerate(dataset):
        try:
            result = process_question.remote(row["question"], row["context"])
            if result == row["answer"]:
                correct += 1
            print(f"Processed {i+1}/{total} | Accuracy: {((correct / (i+1)) * 100):.2f}% | Current: {result == row['answer']}")
        except Exception as e:
            print(f"Error on row {i+1}: {e}")
            print("Pausing for 60 seconds due to rate limit...")
            time.sleep(60) # Wait for a minute before retrying
            try:
                result = process_question.remote(row["question"], row["context"])
                if result == row["answer"]:
                    correct += 1
                print(f"Processed {i+1}/{total} after retry | Accuracy: {((correct / (i+1)) * 100):.2f}% | Current: {result == row['answer']}")
            except Exception as e2:
                print(f"Error on row {i+1} after retry: {e2}")

    accuracy = (correct / total) * 100
    print(f"Final Accuracy: {accuracy:.2f}%")

# Local entrypoint to trigger evaluation
@app.local_entrypoint()
def main():
    evaluate_agent.remote()