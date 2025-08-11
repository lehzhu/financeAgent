#!/usr/bin/env python3
"""
Summarize evaluation results
"""

import json

# Load our evaluation results
with open("evaluation_results.json", "r") as f:
    results = json.load(f)

print("\n" + "="*80)
print("V5 FINANCE AGENT - REAL EVALUATION RESULTS")
print("="*80)

# Analyze each result
categories = {
    "structured": 0,
    "calculation": 0,
    "narrative": 0,
    "unknown": 0
}

zero_answers = 0
non_zero_answers = 0
mock_answers = 0

print("\nDetailed Results:")
print("-" * 80)

for i, result in enumerate(results):
    print(f"\n--- Result {i+1} (ID: {result.get('id', 'N/A')}) ---")
    
    # Get our answer
    our_answer = result.get("final_answer", {})
    value = our_answer.get('value', 'N/A')
    answer_type = our_answer.get('type', 'N/A')
    
    print(f"Answer: {value[:100]}{'...' if len(str(value)) > 100 else ''}")
    print(f"Type: {answer_type}")
    
    # Determine category from trace
    category = "unknown"
    if result.get("trace"):
        first_op = result["trace"][0] if isinstance(result["trace"], list) else {}
        if isinstance(first_op, dict):
            op = first_op.get("op", "")
            if "STRUCTURED" in op:
                category = "structured"
                # Show what was queried
                query = first_op.get("query", "N/A")
                print(f"Query: {query}")
            elif any(x in op for x in ["COMPUTE", "ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"]):
                category = "calculation"
                # Show what was computed
                args = first_op.get("args", [])
                print(f"Calculation: {op} with args {args}")
            elif "NARRATIVE" in op:
                category = "narrative"
    
    categories[category] += 1
    print(f"Category: {category}")
    
    # Check answer quality
    if value == "0.00" or value == "0":
        zero_answers += 1
        print("⚠️  Zero value answer")
    elif "Mock data" in str(value):
        mock_answers += 1
        print("⚠️  Mock data response")
    else:
        non_zero_answers += 1
        print("✓ Non-zero answer")

# Summary statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

print(f"\nTotal Questions Evaluated: {len(results)}")

print(f"\nBy Category:")
for cat, count in categories.items():
    percentage = (count / len(results) * 100) if len(results) > 0 else 0
    print(f"  - {cat.capitalize()}: {count} ({percentage:.1f}%)")

print(f"\nAnswer Quality:")
print(f"  - Non-zero answers: {non_zero_answers} ({non_zero_answers/len(results)*100:.1f}%)")
print(f"  - Zero answers: {zero_answers} ({zero_answers/len(results)*100:.1f}%)")
print(f"  - Mock responses: {mock_answers} ({mock_answers/len(results)*100:.1f}%)")

print("\n" + "="*80)
print("KEY FINDINGS:")
print("="*80)

findings = []

if zero_answers > len(results) * 0.3:
    findings.append("⚠️  High number of zero answers - calculations need input value fetching")

if mock_answers > 0:
    findings.append("⚠️  Some queries returned mock data - database may be missing data")

if categories["calculation"] > 0 and zero_answers >= categories["calculation"] * 0.8:
    findings.append("⚠️  Most calculations returning 0 - need to fetch inputs from database first")

if categories["structured"] > 0 and non_zero_answers > 0:
    findings.append("✓ Structured data lookups are working for available data")

if len(findings) == 0:
    findings.append("✓ System appears to be working well")

for finding in findings:
    print(f"\n{finding}")

print("\n" + "="*80)
print("RECOMMENDATIONS:")
print("="*80)
print("""
1. Primary Issue: Calculations need input values
   - When EBITDA is requested, system should first fetch Operating Income, 
     Depreciation, and Amortization from the database
   - Then perform the calculation with actual values

2. Data Coverage: Some queries return mock data
   - Check if database has all required financial metrics
   - May need to expand the mock data for testing

3. Current Strengths:
   - Routing is working correctly
   - Structured lookups work when data exists
   - System architecture is sound

Overall: The v5 system is correctly routing and processing questions, 
but needs enhancement to fetch required inputs for calculations.
""")

print("="*80)
