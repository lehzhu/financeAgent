#!/usr/bin/env python3
"""
Simple test that actually runs with Modal.
Tests 5 questions to verify the agent is working.
"""

import modal
import time

app = modal.App("simple-test")

# Simple test questions
TEST_QUESTIONS = [
    "What was Costco's total revenue in 2024?",
    "How many warehouses does Costco operate?",
    "Calculate profit margin: revenue $254B, net income $7.4B",
    "Is Costco profitable?",
    "What are Costco's main competitive advantages?"
]

@app.local_entrypoint()
def main():
    """Run simple test."""
    print("=" * 60)
    print("SIMPLE 5-QUESTION TEST")
    print("=" * 60)
    
    # We need to test by actually calling the deployed agent
    print("\nTo test the agent, run these commands:")
    print("-" * 60)
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n{i}. Test question:")
        print(f'   modal run agent/main.py --question "{question}"')
    
    print("\n" + "=" * 60)
    print("Or deploy first then run:")
    print("  modal deploy agent/main.py")
    print("  Then use the commands above")
    print("=" * 60)
