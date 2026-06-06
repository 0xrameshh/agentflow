"""Calculator tool — evaluates basic math expressions safely via AST parsing."""

import ast
import operator

from langchain.tools import tool

# Supported operators for AST evaluation
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(expr: str) -> float:
    """Evaluate a math expression safely using AST (no eval())."""
    tree = ast.parse(expr, mode="eval")

    def _eval_node(node: ast.Expression | ast.BinOp | ast.UnaryOp | ast.Constant) -> float:
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            return _OPERATORS[op_type](left, right)
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _OPERATORS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            return _OPERATORS[op_type](_eval_node(node.operand))
        raise ValueError(f"Unsupported AST node: {type(node).__name__}")

    return _eval_node(tree)


@tool
def calculator(expression: str) -> str:
    """Evaluate a basic math expression. Use for arithmetic only.

    Supports: +, -, *, /, %, **, parentheses, decimal numbers.
    Examples: "2 + 3", "(48 / 6) + 15", "2 ** 10"
    """
    allowed = set("0123456789+-*/().% ")
    if not all(ch in allowed for ch in expression):
        return "Error: expression contains unsupported characters"
    try:
        result = _safe_eval(expression)
        # Return int if result is a whole number
        if result == int(result) and not expression.strip().endswith(".0"):
            return str(int(result))
        return str(result)
    except (ValueError, ZeroDivisionError) as exc:
        return f"Error: {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"Error: {exc}"
