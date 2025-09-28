"""Output formatting utilities for math results - SIMPLIFIED (no LaTeX)"""
from __future__ import annotations
from typing import Any, Dict, List

try:
    import sympy as sp
except Exception:
    sp = None  # type: ignore


def _format_scalar(x: Any, decimals: int | None, scientific: bool) -> Any:
    # SymPy objects - convert to string only
    if sp is not None and isinstance(x, (getattr(sp, 'Basic', tuple()),)):
        try:
            if decimals and isinstance(decimals, int) and decimals >= 0:
                n = decimals
                val = sp.N(x, n)
                try:
                    f = float(val)
                    if scientific:
                        return f"{f:.{n}e}"
                    return round(f, min(n, 12))
                except Exception:
                    return str(val)
        except Exception:
            pass
        return str(x)
    
    # Python numerics
    if isinstance(x, (int, float)):
        if isinstance(decimals, int):
            if scientific:
                return f"{x:.{decimals}e}"
            return round(float(x), decimals)
        return float(x)
    
    # fallback
    return str(x)


def format_output(value: Any, output_format: str = 'string', decimals: int | None = None, scientific: bool = False, exact: bool = False) -> Any:
    """Format scalar/list/matrix-like values - SIMPLIFIED VERSION
    - output_format: ignored (always string)
    - decimals: number of decimals for float/scientific 
    - scientific: True -> scientific notation for floats
    - exact: ignored
    """
    
    # 2D list (matrix)
    if isinstance(value, list) and value and isinstance(value[0], list):
        return [format_output(row, output_format, decimals, scientific, exact) for row in value]
    
    # 1D list
    if isinstance(value, list):
        return [_format_scalar(x, decimals, scientific) for x in value]
    
    # Scalar
    return _format_scalar(value, decimals, scientific)