import modal
from datasets import load_dataset
import os
import time

# Define the Modal app with required dependencies
app = modal.App(
    "finance-evaluate-quick",
    image=modal.Image.debian_slim().pip_install("datasets", "openai"),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

# Quick evaluation function - test 20 questions
@app.function(timeout=600)  # 10 minutes for 20 questions (avg 30s each)
def quick_evaluate_agent():
    # Load the FinanceQA test set
    dataset = load_dataset("AfterQuery/FinanceQA", split="test")
    
    # Get the process_question function from the agent app
    process_question = modal.Function.from_name("finance-agent", "process_question")
    
    correct = 0
    test_size = 20  # Just test 20 questions
    errors = 0
    
    print(f"Quick evaluation of {test_size} questions...")
    print(f"Estimated time: ~{test_size * 2 / 60:.1f} minutes")
    print("-" * 50)
    
    for i in range(test_size):
        row = dataset[i]
        try:
            start_time = time.time()
            result = process_question.remote(row["question"], row["context"])
            elapsed = time.time() - start_time
            
            match = result == row["answer"]
            if match:
                correct += 1
            
            print(f"[{i+1}/{test_size}] Match: {'✓' if match else '✗'} | Time: {elapsed:.1f}s")
            print(f"  Q: {row['question'][:80]}...")
            print(f"  Expected: {row['answer']}")
            print(f"  Got: {result}")
            print(f"  Running accuracy: {(correct/(i+1)*100):.1f}%")
            print()
            
            # Small delay every 5 questions to avoid rate limits
            if (i + 1) % 5 == 0:
                time.sleep(2)
                
        except Exception as e:
            errors += 1
            print(f"[{i+1}/{test_size}] ERROR: {str(e)[:100]}")
            
            if "rate_limit" in str(e).lower():
                print("  -> Waiting 30 seconds for rate limit...")
                time.sleep(30)

    print("=" * 50)
    print(f"QUICK EVALUATION RESULTS:")
    print(f"  Questions tested: {test_size}")
    print(f"  Correct: {correct}")
    print(f"  Errors: {errors}")
    print(f"  Accuracy: {(correct/test_size*100):.1f}%")
    print("=" * 50)

# Local entrypoint
@app.local_entrypoint()
def main():
    quick_evaluate_agent.remote()
