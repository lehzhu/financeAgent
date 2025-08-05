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

# Evaluation function with extended timeout for 148 questions
@app.function(timeout=1800)  # 30 minutes for full evaluation
def evaluate_agent():
    # Load the FinanceQA test set (public dataset, no login required)
    dataset = load_dataset("AfterQuery/FinanceQA", split="test")

    # Get the process_question function from the agent app
    process_question = modal.Function.from_name("finance-agent", "process_question")

    correct = 0
    total = len(dataset)
    errors = 0
    
    print(f"Starting evaluation of {total} questions...")
    print(f"Estimated time: ~{total * 2 / 60:.1f} minutes (with rate limiting)")
    
    for i, row in enumerate(dataset):
        try:
            start_time = time.time()
            result = process_question.remote(row["question"], row["context"])
            elapsed = time.time() - start_time
            
            if result == row["answer"]:
                correct += 1
            
            print(f"[{i+1}/{total}] Accuracy: {((correct / (i+1)) * 100):.2f}% | Match: {result == row['answer']} | Time: {elapsed:.1f}s")
            
            # Add small delay to avoid rate limits
            if (i + 1) % 10 == 0:
                print(f"  -> Progress: {((i+1)/total*100):.1f}% complete, {correct}/{i+1} correct")
                time.sleep(2)  # Small pause every 10 questions
                
        except Exception as e:
            errors += 1
            print(f"[{i+1}/{total}] Error: {str(e)[:100]}")
            
            if "rate_limit" in str(e).lower():
                print("  -> Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                # Retry once
                try:
                    result = process_question.remote(row["question"], row["context"])
                    if result == row["answer"]:
                        correct += 1
                    print(f"  -> Retry successful: {result == row['answer']}")
                except Exception as e2:
                    print(f"  -> Retry failed: {str(e2)[:100]}")

    accuracy = (correct / total) * 100
    print("\n" + "="*50)
    print(f"FINAL RESULTS:")
    print(f"  Total Questions: {total}")
    print(f"  Correct Answers: {correct}")
    print(f"  Errors: {errors}")
    print(f"  Final Accuracy: {accuracy:.2f}%")
    print("="*50)

# Local entrypoint to trigger evaluation
@app.local_entrypoint()
def main():
    evaluate_agent.remote()