import modal
from datasets import load_dataset
import os
import time

# Define the Modal app with required dependencies
app = modal.App(
    "finance-evaluate-test",
    image=modal.Image.debian_slim().pip_install("datasets", "openai"),
    # Optional: Include HF token secret if needed for private datasets
    secrets=[modal.Secret.from_name("hf-token")] if "HF_TOKEN" in os.environ else []
)

# Test evaluation function with just 3 samples
@app.function(timeout=300)
def test_evaluate_agent():
    # Load the FinanceQA test set (public dataset, no login required)
    dataset = load_dataset("AfterQuery/FinanceQA", split="test")
    
    # Get the process_question function from the agent app
    process_question = modal.Function.from_name("finance-agent", "process_question")
    
    correct = 0
    total = 3  # Just test 3 samples
    for i, row in enumerate(dataset.select(range(total))):
        try:
            result = process_question.remote(row["question"], row["context"])
            if result == row["answer"]:
                correct += 1
            print(f"Sample {i+1}/{total}:")
            print(f"  Question: {row['question']}")
            print(f"  Expected: {row['answer']}")
            print(f"  Got: {result}")
            print(f"  Correct: {result == row['answer']}")
            print(f"  Running accuracy: {((correct / (i+1)) * 100):.2f}%")
            print("-" * 50)
        except Exception as e:
            print(f"Error on sample {i+1}: {e}")
    
    accuracy = (correct / total) * 100
    print(f"Final Test Accuracy (3 samples): {accuracy:.2f}%")

# Local entrypoint to trigger evaluation
@app.local_entrypoint()
def main():
    test_evaluate_agent.remote()
