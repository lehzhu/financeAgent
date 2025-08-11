#!/bin/bash

# V5 Finance Agent - Deployment Test Suite
echo "============================================================"
echo "V5 Finance Agent - Deployment Testing"
echo "============================================================"
echo ""

# Test structured data queries
echo "Test 1: Structured Data - Revenue"
modal run deploy.py --question "What was Costco's revenue in 2024?"
echo ""

echo "Test 2: Structured Data - Gross Profit"
modal run deploy.py --question "What was the gross profit in 2024?"
echo ""

# Test narrative queries
echo "Test 3: Narrative - Risk Factors"
modal run deploy.py --question "What are the main risk factors?"
echo ""

echo "Test 4: Narrative - Business Strategy"
modal run deploy.py --question "Describe Costco's business strategy"
echo ""

# Test calculations
echo "Test 5: Simple Calculation - Percentage"
modal run deploy.py --question "What is 15% of 1000000?"
echo ""

echo "Test 6: Simple Calculation - Division"
modal run deploy.py --question "What is 500000 divided by 250?"
echo ""

echo "============================================================"
echo "All tests completed!"
echo "============================================================"
