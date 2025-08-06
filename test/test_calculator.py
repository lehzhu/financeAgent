"""
Test script to demonstrate the improved AST-based calculator functionality
"""

import modal

# Get the Modal app
app = modal.App("test-calculator")

@app.local_entrypoint()
def main():
    """Test various mathematical expressions with the improved calculator."""
    
    # Add parent directory to path to import agent module
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Import the enhanced finance tools
    from agent.main import EnhancedFinanceTools
    
    # Initialize tools
    tools = EnhancedFinanceTools()
    
    # Test cases showcasing the improved calculator
    test_expressions = [
        # Basic arithmetic
        ("2 + 2", "Basic addition"),
        ("10 - 3.5", "Subtraction with decimal"),
        ("5 * 4", "Multiplication"),
        ("20 / 4", "Division"),
        ("10 // 3", "Floor division"),
        ("10 % 3", "Modulo"),
        ("2 ** 8", "Power"),
        
        # Complex expressions
        ("(100 + 50) * 0.3", "Parentheses and mixed operations"),
        ("1000000 * 0.15", "Large numbers (calculating 15% of 1 million)"),
        ("(1000000 - 600000) / 1000000 * 100", "Profit margin calculation"),
        
        # Mathematical functions
        ("sqrt(16)", "Square root"),
        ("abs(-42)", "Absolute value"),
        ("round(3.14159, 2)", "Rounding"),
        ("max(10, 20, 30)", "Maximum"),
        ("min(10, 20, 30)", "Minimum"),
        ("sum([1, 2, 3, 4, 5])", "Sum of list"),
        
        # Logarithmic and exponential
        ("log(100, 10)", "Logarithm base 10 of 100"),
        ("log10(1000)", "Common logarithm"),
        ("exp(1)", "Exponential (e^1)"),
        
        # Trigonometric functions
        ("sin(pi/2)", "Sine of π/2"),
        ("cos(0)", "Cosine of 0"),
        ("tan(pi/4)", "Tangent of π/4"),
        
        # Ceiling and floor
        ("ceil(3.2)", "Ceiling function"),
        ("floor(3.8)", "Floor function"),
        
        # Using mathematical constants
        ("2 * pi * 10", "Circumference of circle with radius 10"),
        ("e ** 2", "e squared"),
        
        # Complex financial calculations
        ("1000 * (1 + 0.05) ** 10", "Compound interest: $1000 at 5% for 10 years"),
        ("50000 * 0.04 / 12", "Monthly interest on $50,000 at 4% annual rate"),
        
        # Invalid expressions (should be rejected)
        ("import os", "Dangerous import statement"),
        ("eval('2+2')", "Dangerous eval"),
        ("__import__('os')", "Dangerous import"),
        ("open('file.txt')", "File operation"),
        ("lambda x: x+1", "Lambda function"),
    ]
    
    print("=" * 80)
    print("TESTING IMPROVED AST-BASED CALCULATOR")
    print("=" * 80)
    print()
    
    for expression, description in test_expressions:
        print(f"Test: {description}")
        print(f"Expression: {expression}")
        result = tools.python_calculator(expression)
        print(f"Result: {result}")
        print("-" * 40)
        print()
    
    # Test integration with the full agent
    print("=" * 80)
    print("TESTING CALCULATOR THROUGH FULL AGENT WORKFLOW")
    print("=" * 80)
    print()
    
    # Import the main process function
    process_question = modal.Function.lookup("finance-agent-main", "process_question_enhanced")
    
    test_questions = [
        "What is 15% of 1 million dollars?",
        "If a company has revenue of $2.5 million and costs of $1.8 million, what is the profit?",
        "Calculate the compound annual growth rate if revenue grew from $100M to $150M over 3 years",
        "What is the monthly payment on a $300,000 loan at 4% annual interest?",
    ]
    
    for question in test_questions:
        print(f"Question: {question}")
        try:
            answer = process_question.remote(question)
            print(f"Answer: {answer}")
        except Exception as e:
            print(f"Error: {str(e)}")
        print("-" * 40)
        print()

if __name__ == "__main__":
    # Run locally
    print("Running calculator tests...")
    main()
