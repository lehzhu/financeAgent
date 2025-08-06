"""
Test script to demonstrate the improved AST-based calculator functionality
This version tests the calculator directly without requiring FAISS
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.main import EnhancedFinanceTools
import ast
import operator
import math

def test_calculator():
    """Test the calculator function directly."""
    
    # Initialize a dummy tools object and copy the calculator method
    tools = type('obj', (object,), {})()
    
    # Copy the python_calculator method implementation
    def python_calculator(expression: str) -> str:
        """Execute safe mathematical calculations using AST parsing."""
        print(f"Calculating: {expression}")
        
        # Define allowed operations
        allowed_operations = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        # Define allowed functions
        allowed_functions = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'sqrt': math.sqrt,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'ceil': math.ceil,
            'floor': math.floor,
        }
        
        # Define allowed constants
        allowed_names = {
            'pi': math.pi,
            'e': math.e,
        }
        
        def safe_eval(node):
            """Recursively evaluate AST nodes safely."""
            if isinstance(node, ast.Constant):  # Python 3.8+
                return node.value
            elif isinstance(node, ast.Num):  # Backward compatibility
                return node.n
            elif isinstance(node, ast.BinOp):
                if type(node.op) in allowed_operations:
                    left = safe_eval(node.left)
                    right = safe_eval(node.right)
                    return allowed_operations[type(node.op)](left, right)
                else:
                    raise ValueError(f"Operation {type(node.op).__name__} not allowed")
            elif isinstance(node, ast.UnaryOp):
                if type(node.op) in allowed_operations:
                    operand = safe_eval(node.operand)
                    return allowed_operations[type(node.op)](operand)
                else:
                    raise ValueError(f"Unary operation {type(node.op).__name__} not allowed")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in allowed_functions:
                    args = [safe_eval(arg) for arg in node.args]
                    return allowed_functions[node.func.id](*args)
                else:
                    func_name = node.func.id if isinstance(node.func, ast.Name) else "unknown"
                    raise ValueError(f"Function '{func_name}' not allowed")
            elif isinstance(node, ast.Name):
                if node.id in allowed_names:
                    return allowed_names[node.id]
                else:
                    raise ValueError(f"Name '{node.id}' not allowed")
            elif isinstance(node, ast.List):
                return [safe_eval(elem) for elem in node.elts]
            elif isinstance(node, ast.Tuple):
                return tuple(safe_eval(elem) for elem in node.elts)
            else:
                raise ValueError(f"AST node type {type(node).__name__} not allowed")
        
        try:
            # Clean the expression
            expr = expression.strip()
            
            # Parse the expression into an AST
            tree = ast.parse(expr, mode='eval')
            
            # Evaluate safely
            result = safe_eval(tree.body)
            
            # Format the result nicely
            if isinstance(result, float):
                # Round to avoid floating point precision issues
                if result == int(result):
                    return str(int(result))
                else:
                    return f"{result:.10g}"  # Use g format to avoid scientific notation for reasonable numbers
            else:
                return str(result)
                
        except SyntaxError as e:
            return f"Syntax error in expression: {str(e)}"
        except ValueError as e:
            return f"Security error: {str(e)}"
        except ZeroDivisionError:
            return "Error: Division by zero"
        except Exception as e:
            return f"Calculation error: {str(e)}"
    
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
        result = python_calculator(expression)
        print(f"Result: {result}")
        print("-" * 40)
        print()

if __name__ == "__main__":
    print("Running simplified calculator tests...")
    test_calculator()
