import modal
from datasets import load_dataset
import time
import asyncio

# Define the test app
app = modal.App(
    "test-parallel-v2",
    image=modal.Image.debian_slim().pip_install("datasets"),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

# Test questions from FinanceQA
TEST_QUESTIONS = [
    {
        "question": "What is Gross Profit in the year ending 2024?",
        "expected": "$32,095 (in millions)",
        "context": None
    },
    {
        "question": "What is unadjusted EBITDA for the year ending in 2024?",
        "expected": "$11,522 (in millions)",
        "context": None
    },
    {
        "question": "Calculate NOPAT if EBIT is 9285 million and tax rate is 24.4%",
        "expected": "7020.54",
        "context": "EBIT for 2024 is $9,285 million, effective tax rate is 24.4%"
    },
    {
        "question": "What is the Operating Profit Margin in the year ending 2024?",
        "expected": "3.65%",
        "context": None
    },
    {
        "question": "What is Costco's total revenue in 2024?",
        "expected": "$254,453 million",
        "context": None
    },
    {
        "question": "What are Costco's shares outstanding (diluted) in 2024?",
        "expected": "445.02 million",
        "context": None
    },
    {
        "question": "Calculate the P/E ratio if stock price is 940 and EPS is 16.56",
        "expected": "56.76",
        "context": "Stock price: $940, Basic EPS: $16.56"
    },
    {
        "question": "What is Costco's long-term debt in 2024?",
        "expected": "$5,360 million",
        "context": None
    },
    {
        "question": "How many warehouses does Costco operate?",
        "expected": "891",
        "context": None
    },
    {
        "question": "What is Costco's Cost of Equity (CAPM) in 2024?",
        "expected": "9.66%",
        "context": None
    }
]

def extract_number(text):
    """Extract numerical value from text for comparison."""
    if text is None:
        return None
    import re
    text = str(text).strip()
    text = text.replace("$", "").replace(",", "").replace("%", "")
    text = text.replace("(in millions)", "").replace("million", "")
    numbers = re.findall(r'-?\d+\.?\d*', text)
    if numbers:
        try:
            return float(numbers[0])
        except:
            return None
    return None

def check_answer(expected, got, tolerance=0.03):
    """Check if answers match with tolerance."""
    if expected == got:
        return True, "exact"
    
    expected_num = extract_number(expected)
    got_num = extract_number(got)
    
    if expected_num is not None and got_num is not None:
        if abs(expected_num - got_num) / max(abs(expected_num), 0.01) < tolerance:
            return True, "numerical"
    
    # Check if the expected number appears anywhere in the answer
    if expected_num is not None and str(int(expected_num)) in str(got):
        return True, "numerical_contains"
    
    # Check if expected is contained in got
    if expected and got and str(expected).lower() in str(got).lower():
        return True, "contains"
    
    return False, "mismatch"

@app.function(timeout=300)
async def test_v2_parallel():
    """Run tests in parallel using the v2 agentic system."""
    from modal import Function
    
    # Get the deployed v2 function
    process_fn = Function.from_name("finance-agent-v2", "process_question_agentic")
    
    print("="*60)
    print("PARALLEL TEST: V2 AGENTIC SYSTEM")
    print("Testing 10 questions in parallel...")
    print("="*60)
    
    start_time = time.time()
    
    # Create all the async calls at once (parallel execution)
    async def process_question(idx, q):
        q_start = time.time()
        try:
            result = await process_fn.remote.aio(
                question=q["question"], 
                context=q.get("context")
            )
            q_time = time.time() - q_start
            return idx, result, q_time, None
        except Exception as e:
            q_time = time.time() - q_start
            return idx, None, q_time, str(e)
    
    # Launch all questions in parallel
    tasks = [process_question(i, q) for i, q in enumerate(TEST_QUESTIONS)]
    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    
    # Process results
    correct = 0
    details = []
    
    for idx, answer, q_time, error in results:
        q = TEST_QUESTIONS[idx]
        
        if error:
            match_status = "ERROR"
            match_type = error[:50]
        else:
            is_match, match_type = check_answer(q["expected"], answer)
            if is_match:
                correct += 1
                match_status = "✓"
            else:
                match_status = "✗"
        
        details.append({
            "num": idx + 1,
            "question": q["question"][:50] + "...",
            "expected": q["expected"],
            "got": str(answer)[:50] if answer else "ERROR",
            "match": match_status,
            "type": match_type,
            "time": q_time
        })
    
    # Print results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    for d in details:
        print(f"\n[Q{d['num']}] {d['match']} ({d['type']}) - {d['time']:.1f}s")
        print(f"  Question: {d['question']}")
        print(f"  Expected: {d['expected']}")
        print(f"  Got: {d['got']}")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Correct: {correct}/10 ({correct*10}%)")
    print(f"Total time: {total_time:.1f}s (parallel)")
    print(f"Average time per question: {total_time/10:.1f}s")
    print(f"Time if run sequentially: ~{sum(r[2] for r in results):.1f}s")
    print(f"Speedup from parallelization: {sum(r[2] for r in results)/total_time:.1f}x")
    print("="*60)

@app.local_entrypoint()
def main():
    """Run the parallel test."""
    import asyncio
    asyncio.run(test_v2_parallel.remote.aio())
