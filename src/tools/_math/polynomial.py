"""Polynomial operations using SymPy"""
from __future__ import annotations
from typing import Dict, Any, List

try:
    import sympy as sp
except Exception:
    sp = None  # type: ignore


def _ensure_sympy() -> Dict[str, Any] | None:
    if sp is None:
        return {"error": "SymPy not available. Install sympy to use polynomial ops."}
    return None


def poly_roots(coeffs: List[float]) -> Dict[str, Any]:
    err = _ensure_sympy();
    if err: return err
    try:
        x = sp.Symbol('x')
        p = sp.Poly(coeffs, x)
        roots = p.nroots()
        return {"result": [str(r) for r in roots]}
    except Exception as e:
        return {"error": f"poly_roots error: {e}"}


def poly_factor(expression: str) -> Dict[str, Any]:
    err = _ensure_sympy();
    if err: return err
    try:
        expr = sp.sympify(expression)
        fact = sp.factor(expr)
        return {"result": str(fact)}
    except Exception as e:
        return {"error": f"poly_factor error: {e}"}


def poly_expand(expression: str) -> Dict[str, Any]:
    err = _ensure_sympy();
    if err: return err
    try:
        expr = sp.sympify(expression)
        ex = sp.expand(expr)
        return {"result": str(ex)}
    except Exception as e:
        return {"error": f"poly_expand error: {e}"}