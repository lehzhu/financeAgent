"""
V5 Phase 1: Simple Calculator Agent

The simplest possible calculator to handle basic math operations.
Focus: Get something working first, then improve.
"""

import re
import ast
import operator


class SimpleCalculator:
    """Simple calculator for basic math operations."""
    
    def __init__(self):
        # Safe operations for AST evaluation
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
    
    def calculate(self, question):
        """Main calculation function."""
        question_lower = question.lower().strip()
        
        # Handle percentage calculations
        if "%" in question or "percent" in question_lower:
            return self._handle_percentage(question_lower)
        
        # Handle growth rate calculations
        if "growth rate" in question_lower:
            return self._handle_growth_rate(question_lower)
        
        # Handle ratio calculations
        if "ratio" in question_lower:
            return self._handle_ratio(question_lower)
        
        # Handle basic arithmetic expressions
        if any(op in question for op in ['+', '-', '*', '/', '=']):
            return self._handle_arithmetic(question_lower)
        
        return "I don't know how to calculate that"
    
    def _handle_percentage(self, question):
        """Handle percentage calculations like '15% of 100'."""
        # Pattern: "X% of Y" or "X percent of Y"
        pattern = r'(\d+(?:\.\d+)?)%?\s*(?:percent\s+)?of\s+(\d+(?:\.\d+)?)'
        match = re.search(pattern, question)
        
        if match:
            percentage = float(match.group(1))
            value = float(match.group(2))
            result = (percentage / 100) * value
            
            # Format result
            if result == int(result):
                return str(int(result))
            else:
                return f"{result:.2f}"
        
        return "Cannot parse percentage calculation"
    
    def _handle_growth_rate(self, question):
        """Handle growth rate calculations like 'growth rate from 100 to 120'."""
        # Pattern: "from X to Y"
        pattern = r'from\s+(\d+(?:\.\d+)?)\s+to\s+(\d+(?:\.\d+)?)'
        match = re.search(pattern, question)
        
        if match:
            old_value = float(match.group(1))
            new_value = float(match.group(2))
            growth_rate = ((new_value - old_value) / old_value) * 100
            return f"{growth_rate:.1f}%"
        
        return "Cannot parse growth rate calculation"
    
    def _handle_ratio(self, question):
        """Handle ratio calculations like 'ratio 50:25'."""
        # Pattern: "X:Y" or "X to Y"
        colon_pattern = r'(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)'
        to_pattern = r'(\d+(?:\.\d+)?)\s+to\s+(\d+(?:\.\d+)?)'
        
        match = re.search(colon_pattern, question) or re.search(to_pattern, question)
        
        if match:
            num1 = float(match.group(1))
            num2 = float(match.group(2))
            ratio = num1 / num2
            
            if ratio == int(ratio):
                return str(int(ratio))
            else:
                return f"{ratio:.2f}"
        
        return "Cannot parse ratio calculation"
    
    def _handle_arithmetic(self, question):
        """Handle basic arithmetic expressions."""
        # Extract mathematical expressions
        # Look for patterns like "what is 2 + 2" or "2 + 2 * 3"
        
        # Try to find the mathematical part
        math_patterns = [
            r'what\s+is\s+([0-9+\-*/.\s()]+)',  # "what is X + Y"
            r'calculate\s+([0-9+\-*/.\s()]+)',   # "calculate X + Y"
            r'^([0-9+\-*/.\s()]+)$',             # Just "X + Y"
        ]
        
        for pattern in math_patterns:
            match = re.search(pattern, question)
            if match:
                expression = match.group(1).strip()
                result = self._safe_eval(expression)
                if result is not None:
                    if isinstance(result, float) and result == int(result):
                        return str(int(result))
                    else:
                        return str(result)
        
        return "Cannot parse arithmetic expression"
    
    def _safe_eval(self, expression):
        """Safely evaluate mathematical expressions using AST."""
        try:
            # Clean the expression
            expression = expression.replace(' ', '')
            
            # Parse into AST
            tree = ast.parse(expression, mode='eval')
            
            # Evaluate safely
            return self._eval_node(tree.body)
            
        except Exception as e:
            print(f"Error evaluating '{expression}': {e}")
            return None
    
    def _eval_node(self, node):
        """Recursively evaluate AST nodes."""
        if isinstance(node, ast.Constant):  # Numbers
            return node.value
        elif isinstance(node, ast.Num):  # Backward compatibility
            return node.n
        elif isinstance(node, ast.BinOp):  # Binary operations
            if type(node.op) in self.operators:
                left = self._eval_node(node.left)
                right = self._eval_node(node.right)
                return self.operators[type(node.op)](left, right)
            else:
                raise ValueError(f"Unsupported operation: {type(node.op)}")
        elif isinstance(node, ast.UnaryOp):  # Unary operations
            if type(node.op) in self.operators:
                operand = self._eval_node(node.operand)
                return self.operators[type(node.op)](operand)
            else:
                raise ValueError(f"Unsupported unary operation: {type(node.op)}")
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")


# Create a simple interface function
def phase1_calculator(question):
    """Phase 1 calculator agent function."""
    calc = SimpleCalculator()
    return calc.calculate(question)


# Test the calculator
if __name__ == "__main__":
    calc = SimpleCalculator()
    
    test_questions = [
        "What is 15% of 100?",
        "Calculate 25% of 200",
        "What is the growth rate from 100 to 120?",
        "Calculate the ratio 50:25",
        "What is 2 + 2 * 3?",
    ]
    
    print("Testing Phase 1 Calculator:")
    print("=" * 50)
    
    for question in test_questions:
        result = calc.calculate(question)
        print(f"Q: {question}")
        print(f"A: {result}")
        print()
