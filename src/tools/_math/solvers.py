"""Equation solvers and simple optimization (SymPy-based)"""
from __future__ import annotations
from typing import Dict, Any, List

try:
    import sympy as sp
except Exception:
    sp = None  # type: ignore


def _ensure_sympy() -> Dict[str, Any] | None:
    if sp is None:
        return {"error": "SymPy not available. Install sympy to use solvers."}
    return None


def _sympify_expr(expr_str: str):
    return sp.sympify(expr_str)


def _parse_equation(eq_str: str):
    # Accept forms like "expr = expr" or just "expr" meaning expr = 0
    if "=" in eq_str:
        parts = eq_str.split("=")
        if len(parts) != 2:
            raise ValueError("Invalid equation format")
        lhs = sp.sympify(parts[0])
        rhs = sp.sympify(parts[1])
        return sp.Eq(lhs, rhs)
    return sp.Eq(sp.sympify(eq_str), 0)


def solve_eq(equation: str, variable: str) -> Dict[str, Any]:
    err = _ensure_sympy();  
    if err: return err
    try:
        var = sp.Symbol(variable)
        eq = _parse_equation(equation)
        sols = sp.solve(eq, var)
        return {"solutions": [str(s) for s in sols]}
    except Exception as e:
        return {"error": f"solve_eq error: {e}"}


def solve_system(equations: List[str], variables: List[str]) -> Dict[str, Any]:
    err = _ensure_sympy();  
    if err: return err
    try:
        vars_syms = [sp.Symbol(v) for v in variables]
        eqs = [_parse_equation(e) for e in equations]
        sols = sp.solve(eqs, vars_syms, dict=True)
        out = [{str(k): str(v) for k, v in sol.items()} for sol in sols]
        return {"solutions": out}
    except Exception as e:
        return {"error": f"solve_system error: {e}"}


def nsolve_expr(expression: str, variable: str, guess: float | int) -> Dict[str, Any]:
    err = _ensure_sympy();  
    if err: return err
    try:
        var = sp.Symbol(variable)
        expr = sp.sympify(expression)
        val = sp.nsolve(expr, var, guess)
        return {"root": float(val)}
    except Exception as e:
        return {"error": f"nsolve error: {e}"}


def root_find(expression: str, variable: str, x0: float, tol: float = 1e-7, max_iter: int = 50) -> Dict[str, Any]:
    err = _ensure_sympy();  
    if err: return err
    try:
        var = sp.Symbol(variable)
        expr = sp.sympify(expression)
        dexpr = sp.diff(expr, var)
        f = sp.lambdify(var, expr, 'math')
        df = sp.lambdify(var, dexpr, 'math')
        x = float(x0)
        for _ in range(max_iter):
            fx = f(x)
            dfx = df(x)
            if dfx == 0:
                return {"error": "Zero derivative encountered", "x": x}
            x_new = x - fx / dfx
            if abs(x_new - x) < tol:
                return {"root": x_new}
            x = x_new
        return {"root": x}
    except Exception as e:
        return {"error": f"root_find error: {e}"}


def optimize_1d(expression: str, variable: str, a: float, b: float, goal: str = 'min', tol: float = 1e-6, max_iter: int = 100) -> Dict[str, Any]:
    """Golden-section search for min or max on [a,b]"""
    err = _ensure_sympy();  
    if err: return err
    
    # Validate interval
    if a >= b:
        return {"error": f"Invalid interval: a ({a}) must be less than b ({b})"}
    
    try:
        import math
        var = sp.Symbol(variable)
        expr = sp.sympify(expression)
        f = sp.lambdify(var, expr, 'math')
        phi = (1 + math.sqrt(5)) / 2
        invphi = 1 / phi
        # Initialize points
        c = b - (b - a) * invphi
        d = a + (b - a) * invphi
        fc = f(c)
        fd = f(d)
        if goal == 'max':
            fc, fd = -fc, -fd
        it = 0
        while abs(b - a) > tol and it < max_iter:
            if fc < fd:
                b, fd = d, fc
                d = c
                c = b - (b - a) * invphi
                fc = f(c)
                if goal == 'max':
                    fc = -fc
            else:
                a, fc = c, fd
                c = d
                d = a + (b - a) * invphi
                fd = f(d)
                if goal == 'max':
                    fd = -fd
            it += 1
        x_opt = (a + b) / 2
        y_opt = f(x_opt)
        return {"x": x_opt, "y": y_opt}
    except Exception as e:
        return {"error": f"optimize_1d error: {e}"}