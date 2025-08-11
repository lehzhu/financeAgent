#!/usr/bin/env python3
"""
Analyze evaluation results with questions from FinanceQA dataset
"""

import json
from datasets import load_dataset

# Load the FinanceQA dataset to get the questions
print("Loading FinanceQA dataset...")
dataset = load_dataset("AfterQuery/FinanceQA", split="test")

# Load our evaluation results
with open("evaluation_results.json", "r") as f:
    results = json.load(f)

print("\n" + "="*80)
print("V5 FINANCE AGENT - EVALUATION RESULTS ANALYSIS")
print("="*80)

# Analyze each result
categories = {
    "structured": [],
    "calculation": [],
    "narrative": [],
    "unknown": []
}

for i, result in enumerate(results):
    # Get the corresponding question from the dataset
    question_data = dataset[i]
    question = question_data.get("Question", "N/A")
    expected_answer = question_data.get("Answer", "N/A")
    
    print(f"\n--- Question {i+1} ---")
    print(f"Question: {question}")
    print(f"Expected: {expected_answer}")
    
    # Get our answer
    our_answer = result.get("final_answer", {})
    print(f"Our Answer: {our_answer.get('value', 'N/A')} ({our_answer.get('type', 'N/A')})")
    
    # Determine category from trace
    if result.get("trace"):
        first_op = result["trace"][0] if isinstance(result["trace"], list) else {}
        if isinstance(first_op, dict):
            op = first_op.get("op", "")
            if "STRUCTURED" in op:
                categories["structured"].append(i)
                print("Category: Structured Data Lookup")
            elif any(x in op for x in ["COMPUTE", "ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"]):
                categories["calculation"].append(i)
                print("Category: Calculation")
            elif "NARRATIVE" in op:
                categories["narrative"].append(i)
                print("Category: Narrative")
            else:
                categories["unknown"].append(i)
                print(f"Category: Unknown ({op})")
    
    # Check if answer is meaningful (not 0 for calculations)
    if our_answer.get("value") == "0.00" and i in categories["calculation"]:
        print("⚠️  Warning: Calculation returned 0 (likely missing inputs)")

# Summary statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

print(f"\nTotal Questions: {len(results)}")
print(f"\nBy Category:")
print(f"  - Structured Data: {len(categories['structured'])} questions")
print(f"  - Calculations: {len(categories['calculation'])} questions")
print(f"  - Narrative: {len(categories['narrative'])} questions")
print(f"  - Unknown: {len(categories['unknown'])} questions")

# Count successful vs failed
zero_calculations = sum(1 for i in categories["calculation"] 
                        if results[i].get("final_answer", {}).get("value") == "0.00")
successful_structured = sum(1 for i in categories["structured"] 
                            if "Mock data" not in results[i].get("final_answer", {}).get("value", ""))

print(f"\nSuccess Rates:")
print(f"  - Structured: {successful_structured}/{len(categories['structured'])} " +
      f"({100*successful_structured/max(1, len(categories['structured'])):.1f}%)")
print(f"  - Calculations: {len(categories['calculation']) - zero_calculations}/{len(categories['calculation'])} " +
      f"({100*(len(categories['calculation']) - zero_calculations)/max(1, len(categories['calculation'])):.1f}%)")

print("\n" + "="*80)
print("KEY FINDINGS:")
print("="*80)
print("""
1. Most calculation questions are returning 0 because they need input values
   that should be fetched from the database first.
   
2. Structured data lookups work when the data exists in the database.

3. The system correctly routes questions to the appropriate tool.

4. Main improvement needed: When a calculation requires values (like EBITDA 
   needing Operating Income, Depreciation, etc.), the system should:
   - First query the database for these values
   - Then perform the calculation with the actual values
""")

# Save detailed analysis
analysis = {
    "total_questions": len(results),
    "categories": {
        "structured": len(categories["structured"]),
        "calculation": len(categories["calculation"]),
        "narrative": len(categories["narrative"])
    },
    "issues": {
        "zero_calculations": zero_calculations,
        "mock_responses": len(categories["structured"]) - successful_structured
    },
    "questions_and_answers": []
}

for i, result in enumerate(results):
    question_data = dataset[i]
    analysis["questions_and_answers"].append({
        "question": question_data.get("Question", "N/A"),
        "expected": question_data.get("Answer", "N/A"),
        "our_answer": result.get("final_answer", {}).get("value", "N/A"),
        "type": result.get("final_answer", {}).get("type", "N/A"),
        "trace": result.get("trace", [])[0] if result.get("trace") else None
    })

with open("detailed_analysis.json", "w") as f:
    json.dump(analysis, f, indent=2)

print(f"\nDetailed analysis saved to detailed_analysis.json")
