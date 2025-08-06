import modal
import time

app = modal.App(
    "test-v3",
    secrets=[modal.Secret.from_name("openai-key-1")]
)

TEST_QUESTIONS = [
    {"question": "What is Gross Profit in the year ending 2024?", "expected": "$32,095 (in millions)"},
    {"question": "What is unadjusted EBITDA for the year ending in 2024?", "expected": "$11,522 (in millions)"},
    {"question": "Calculate NOPAT if EBIT is 9285 million and tax rate is 24.4%", "expected": "7020.54"},
    {"question": "What is the Operating Profit Margin in the year ending 2024?", "expected": "3.65%"},
    {"question": "What is Costco's total revenue in 2024?", "expected": "$254,453 million"},
    {"question": "What are Costco's shares outstanding (diluted) in 2024?", "expected": "445.02 million"},
    {"question": "Calculate the P/E ratio if stock price is 940 and EPS is 16.56", "expected": "56.76"},
    {"question": "What is Costco's long-term debt in 2024?", "expected": "$5,360 million"},
    {"question": "How many warehouses does Costco operate?", "expected": "891"},
    {"question": "What is Costco's Cost of Equity (CAPM) in 2024?", "expected": "9.66%"}
]

@app.function(timeout=300)
def test_v3():
    from modal import Function
    
    process_fn = Function.from_name("finance-agent-v3", "process_question_fullcontext")
    
    print("="*60)
    print("V3 TEST: FULL CONTEXT WINDOW APPROACH")
    print(f"Document size: ~55k tokens in every request")
    print("="*60)
    
    start = time.time()
    correct = 0
    
    for i, q in enumerate(TEST_QUESTIONS, 1):
        q_start = time.time()
        try:
            result = process_fn.remote(q["question"])
            q_time = time.time() - q_start
            
            # Simple check
            match = q["expected"].lower() in str(result).lower() or \
                   str(int(float(q["expected"].replace("$","").replace(",","").replace("%","").split()[0]))) in str(result)
            
            if match:
                correct += 1
                status = "✅"
            else:
                status = "❌"
            
            print(f"\n[Q{i}] {status} - {q_time:.1f}s")
            print(f"  Expected: {q['expected']}")
            print(f"  Got: {str(result)[:100]}")
            
        except Exception as e:
            print(f"\n[Q{i}] ERROR: {e}")
    
    total_time = time.time() - start
    
    print("\n" + "="*60)
    print(f"V3 Results: {correct}/10 ({correct*10}%)")
    print(f"Total time: {total_time:.1f}s")
    print(f"Avg per question: {total_time/10:.1f}s")
    print("\nCost Analysis:")
    print(f"  ~55k tokens input x 10 questions = 550k input tokens")
    print(f"  GPT-4o: $2.50/1M input tokens = ~$1.38 for this test")
    print(f"  V2 approach: ~5k tokens avg = ~$0.13 for this test")
    print("="*60)

@app.local_entrypoint()
def main():
    test_v3.remote()
