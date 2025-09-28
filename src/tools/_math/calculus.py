"""Advanced calculus: limits, series, gradient, jacobian, hessian"""
from __future__ import annotations
from typing import Dict, Any, List

try:
    import sympy as sp
except Exception:
    sp = None  # type: ignore


def _ensure_sympy() -> Dict[str, Any] | None:
    if sp is None:
        return {"error": "SymPy not available. Install sympy to use calculus ops."}
    return None


def limit(expression: str, variable: str, point: Any, direction: str = '+') -> Dict[str, Any]:
    err = _ensure_sympy();
    if err: return err
    try:
        var = sp.Symbol(variable)
        expr = sp.sympify(expression)
        res = sp.limit(expr, var, point, dir=direction)
        return {"result": str(res)}
    except Exception as e:
        return {"error": f"limit error: {e}"}


def series(expression: str, variable: str, point: Any = 0, order: int = 6) -> Dict[str, Any]:
    err = _ensure_sympy();
    if err: return err
    try:
        var = sp.Symbol(variable)
        expr = sp.sympify(expression)
        ser = sp.series(expr, var, point, order)
        return {"result": str(ser.removeO())}
    except Exception as e:
        return {"error": f"series error: {e}"}


def gradient(expression: str, variables: List[str]) -> Dict[str, Any]:
    err = _ensure_sympy();
    if err: return err
    try:
        vars_syms = [sp.Symbol(v) for v in variables]
        expr = sp.sympify(expression)
        grads = [sp.diff(expr, v) for v in vars_syms]
        return {"result": [str(g) for g in grads]}
    except Exception as e:
        return {"error": f"gradient error: {e}"}


def jacobian(expressions: List[str], variables: List[str]) -> Dict[str, Any]:
    err = _ensure_sympy();
    if err: return err
    try:
        exprs = [sp.sympify(e) for e in expressions]
        vars_syms = [sp.Symbol(v) for v in variables]
        J = sp.Matrix(exprs).jacobian(vars_syms)
        return {"result": [[str(x) for x in J.row(i)] for i in range(J.rows)]}
    except Exception as e:
        return {"error": f"jacobian error: {e}"}


def hessian(expression: str, variables: List[str]) -> Dict[str, Any]:
    err = _ensure_sympy();
    if err: return err
    try:
        vars_syms = [sp.Symbol(v) for v in variables]
        expr = sp.sympify(expression)
        H = sp.hessian(expr, vars_syms)
        return {"result": [[str(x) for x in H.row(i)] for i in range(H.rows)]}
    except Exception as e:
        return {"error": f"hessian error: {e}"}