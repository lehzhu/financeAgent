import ast
import operator
import math
from typing import Union

class CalculationError(Exception):
    pass

# Allowed operations and functions for safe evaluation
_ALLOWED_OPS = {
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

_ALLOWED_FUNCS = {
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

_ALLOWED_NAMES = {
    'pi': math.pi,
    'e': math.e,
}


def _safe_eval(node) -> Union[int, float]:
    if isinstance(node, ast.Constant):  # py3.8+
        val = node.value
        if isinstance(val, (int, float)):
            return val
        raise CalculationError("Only numeric constants are allowed")
    if isinstance(node, ast.Num):  # legacy
        return node.n
    if isinstance(node, ast.BinOp):
        if type(node.op) not in _ALLOWED_OPS:
            raise CalculationError(f"Operation {type(node.op).__name__} not allowed")
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        # Explicitly handle division by zero
        if isinstance(node.op, (ast.Div, ast.FloorDiv)) and right == 0:
            raise ZeroDivisionError("division by zero")
        return _ALLOWED_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp):
        if type(node.op) not in _ALLOWED_OPS:
            raise CalculationError(f"Unary operation {type(node.op).__name__} not allowed")
        operand = _safe_eval(node.operand)
        return _ALLOWED_OPS[type(node.op)](operand)
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _ALLOWED_FUNCS:
            args = [_safe_eval(arg) for arg in node.args]
            return _ALLOWED_FUNCS[node.func.id](*args)
        func_name = node.func.id if isinstance(node.func, ast.Name) else "unknown"
        raise CalculationError(f"Function '{func_name}' not allowed")
    if isinstance(node, ast.Name):
        if node.id in _ALLOWED_NAMES:
            return _ALLOWED_NAMES[node.id]
        raise CalculationError(f"Name '{node.id}' not allowed")
    if isinstance(node, ast.List):
        return [_safe_eval(elem) for elem in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_safe_eval(elem) for elem in node.elts)
    raise CalculationError(f"AST node type {type(node).__name__} not allowed")


def evaluate_expression(expression: str) -> str:
    """
    Evaluate a mathematical expression safely using AST.
    Returns a stringified result. Handles division by zero and security errors.
    """
    expr = (expression or "").strip()
    if not expr:
        return ""
    try:
        tree = ast.parse(expr, mode='eval')
        result = _safe_eval(tree.body)
        if isinstance(result, float):
            # Nicely format floats to avoid excessive precision/scientific notation for common ranges
            if result == int(result):
                return str(int(result))
            return f"{result:.10g}"
        return str(result)
    except ZeroDivisionError:
        return "Error: Division by zero"
    except SyntaxError as e:
        return f"Syntax error: {e.msg}"
    except CalculationError as e:
        return f"Security error: {str(e)}"
    except Exception as e:
        return f"Calculation error: {str(e)}"

