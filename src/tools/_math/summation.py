"""Summations and products using SymPy (finite and infinite)"""
from __future__ import annotations
from typing import Dict, Any

try:
    import sympy as sp
except Exception:
    sp = None  # type: ignore


def _ensure_sympy() -> Dict[str, Any] | None:
    if sp is None:
        return {"error": "SymPy not available. Install sympy to use summations/products."}
    return None


def sum_finite(expression: str, index: str, start, end) -> Dict[str, Any]:
    err = _ensure_sympy();
    if err: return err
    try:
        i = sp.Symbol(index)
        expr = sp.sympify(expression)
        a = sp.sympify(start)
        b = sp.sympify(end)
        s = sp.summation(expr, (i, a, b))
        return {"result": str(s)}
    except Exception as e:
        return {"error": f"sum_finite error: {e}"}


def product_finite(expression: str, index: str, start, end) -> Dict[str, Any]:
    err = _ensure_sympy();
    if err: return err
    try:
        i = sp.Symbol(index)
        expr = sp.sympify(expression)
        a = sp.sympify(start)
        b = sp.sympify(end)
        p = sp.product(expr, (i, a, b))
        return {"result": str(p)}
    except Exception as e:
        return {"error": f"product_finite error: {e}"}


def sum_infinite(expression: str, index: str, start) -> Dict[str, Any]:
    err = _ensure_sympy();
    if err: return err
    try:
        i = sp.Symbol(index)
        expr = sp.sympify(expression)
        a = sp.sympify(start)
        s = sp.summation(expr, (i, a, sp.oo))
        return {"result": str(s)}
    except Exception as e:
        return {"error": f"sum_infinite error: {e}"}