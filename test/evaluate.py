import modal
from datasets import load_dataset
import os
import re
import time

# Define the Modal app with required dependencies
app = modal.App(
    "finance-evaluate",
    image=modal.Image.debian_slim().pip_install("datasets", "openai"),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

def extract_number(text):
    """Extract numerical value from text, handling various formats."""
    if text is None:
        return None
    
    # Convert to string and clean
    text = str(text).strip()
    
    # Look for patterns like "is $X" or "is X" or "= X"
    import re
    
    # First try to find values after "is", "=", or ":"
    patterns = [
        r'(?:is|equals?|=|:)\s*\$?([\d,]+(?:\.\d+)?)',
        r'\$([\d,]+(?:\.\d+)?)\s*(?:million|billion)?',
        r'([\d,]+(?:\.\d+)?)\s*(?:million|billion)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Clean and return the number
            num_str = match.group(1).replace(",", "")
            try:
                value = float(num_str)
                # Handle million/billion
                if "million" in text.lower():
                    value *= 1000000 if value < 1000 else 1  # Avoid double conversion
                elif "billion" in text.lower():
                    value *= 1000000000 if value < 1000000 else 1
                return value
            except:
                pass
    
    # Fallback: get the last number in the text (often the answer)
    numbers = re.findall(r'\d+[,\d]*(?:\.\d+)?', text)
    if numbers:
        # Skip years (4 digits starting with 19 or 20)
        for num in reversed(numbers):
            num_clean = num.replace(",", "")
            if len(num_clean) == 4 and num_clean[:2] in ['19', '20']:
                continue
            try:
                return float(num_clean)
            except:
                pass
    
    return None

def answers_match(expected, got, tolerance=0.02):
    """Check if answers match with some tolerance for numerical values."""
    if expected == got:
        return True
    
    # Try numerical comparison
    expected_num = extract_number(expected)
    got_num = extract_number(got)
    
    if expected_num is not None and got_num is not None:
        # Allow 2% tolerance for numerical answers
        if abs(expected_num - got_num) / max(abs(expected_num), 0.01) < tolerance:
            return True
    
    # Check for Yes/No questions
    expected_lower = str(expected).lower().strip()
    got_lower = str(got).lower().strip()
    
    if expected_lower in ["yes", "no"]:
        if expected_lower in got_lower:
            return True
    
    # Check if the expected answer is contained in the response
    if expected_lower in got_lower:
        return True
    
    return False

# Evaluation function with smart matching
@app.function(timeout=1800)  # 30 minutes for full evaluation
def evaluate_agent(test_size=30):
    """Evaluate the finance agent with smart answer matching.
    
    Args:
        test_size: Number of questions to test (default: 30, max: 148 for full dataset)
    """
    # Load the FinanceQA test set
    dataset = load_dataset("AfterQuery/FinanceQA", split="test")
    
    # Import Modal to call the deployed agent
    import modal
    
    # Get the deployed function
    process_question = modal.Function.lookup("finance-agent-main", "process_question_enhanced")
    
    # Limit test_size to dataset size
    test_size = min(test_size, len(dataset))
    
    correct = 0
    errors = 0
    close_matches = 0
    
    print("="*60)
    print("FINANCE AGENT EVALUATION")
    print(f"Testing {test_size} questions with smart matching")
    print(f"Dataset size: {len(dataset)} questions")
    print("="*60)
    print()
    
    for i in range(test_size):
        row = dataset[i]
        try:
            start_time = time.time()
            result = process_question.remote(row["question"], row.get("context", ""))
            elapsed = time.time() - start_time
            
            # Check if answers match
            exact_match = (result == row["answer"])
            smart_match = answers_match(row["answer"], result)
            
            if smart_match:
                correct += 1
                if not exact_match:
                    close_matches += 1
            
            # Detailed output for transparency
            print(f"[Question {i+1}/{test_size}]")
            print(f"Q: {row['question'][:100]}...")
            print(f"Expected: {row['answer']}")
            print(f"Got:      {result}")
            
            # Show numerical extraction for debugging
            exp_num = extract_number(row["answer"])
            got_num = extract_number(result)
            if exp_num is not None and got_num is not None:
                diff = abs(exp_num - got_num) / max(abs(exp_num), 0.01) * 100
                print(f"Numbers:  {exp_num} vs {got_num} (diff: {diff:.2f}%)")
            
            print(f"Match:    {'✓ EXACT' if exact_match else '✓ SMART' if smart_match else '✗ NO MATCH'}")
            print(f"Time:     {elapsed:.1f}s")
            print(f"Running:  {(correct/(i+1)*100):.1f}% accurate")
            print("-"*60)
            print()
            
            # Small delay every 5 questions
            if (i + 1) % 5 == 0:
                time.sleep(2)
                
        except Exception as e:
            errors += 1
            print(f"[Question {i+1}/{test_size}] ERROR")
            print(f"Error: {str(e)[:200]}")
            print("-"*60)
            print()
            
            if "rate_limit" in str(e).lower():
                print("Waiting 30 seconds for rate limit...")
                time.sleep(30)

    print("="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Questions tested:  {test_size}")
    print(f"Correct answers:   {correct} ({correct/test_size*100:.1f}%)")
    print(f"  - Exact matches: {correct - close_matches}")
    print(f"  - Smart matches: {close_matches}")
    print(f"Errors:           {errors}")
    print(f"Final Accuracy:   {(correct/test_size*100):.1f}%")
    print("="*60)

# Local entrypoint
@app.local_entrypoint()
def main(test_size: int = 30):
    """Run evaluation with specified number of questions.
    
    Args:
        test_size: Number of questions to test (default: 30)
    """
    evaluate_agent.remote(test_size)
