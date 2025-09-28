"""Linear algebra extensions: pinv, cond, trace, nullspace, decompositions"""
from __future__ import annotations
from typing import Dict, Any

try:
    import sympy as sp
except Exception:
    sp = None  # type: ignore


def _ensure_sympy() -> Dict[str, Any] | None:
    if sp is None:
        return {"error": "SymPy not available. Install sympy to use linear algebra extensions."}
    return None


def _to_matrix(M) -> "sp.Matrix":
    if isinstance(M, sp.Matrix):
        return M
    return sp.Matrix(M)


def pinv(A):
    err = _ensure_sympy();
    if err: return err
    try:
        M = _to_matrix(A)
        R = M.pinv()
        return {"result": [[str(x) for x in R.row(i)] for i in range(R.rows)]}
    except Exception as e:
        return {"error": f"pinv error: {e}"}


def cond(A, p: int | float | str = 2):
    err = _ensure_sympy();
    if err: return err
    try:
        M = _to_matrix(A)
        c = M.condition_number(p)
        try:
            c = float(c)
        except Exception:
            c = str(c)
        return {"result": c}
    except Exception as e:
        return {"error": f"cond error: {e}"}


def trace(A):
    err = _ensure_sympy();
    if err: return err
    try:
        M = _to_matrix(A)
        t = M.trace()
        try:
            t = float(t)
        except Exception:
            t = str(t)
        return {"result": t}
    except Exception as e:
        return {"error": f"trace error: {e}"}


def nullspace(A):
    err = _ensure_sympy();
    if err: return err
    try:
        M = _to_matrix(A)
        N = M.nullspace()
        out = []
        for v in N:
            out.append([str(x) for x in list(v)])
        return {"result": out}
    except Exception as e:
        return {"error": f"nullspace error: {e}"}


def lu(A):
    err = _ensure_sympy();
    if err: return err
    try:
        M = _to_matrix(A)
        L, U, _ = M.LUdecomposition()
        return {
            "result": {
                "L": [[str(x) for x in L.row(i)] for i in range(L.rows)],
                "U": [[str(x) for x in U.row(i)] for i in range(U.rows)]
            }
        }
    except Exception as e:
        return {"error": f"lu error: {e}"}


def qr(A):
    err = _ensure_sympy();
    if err: return err
    try:
        M = _to_matrix(A)
        Q, R = M.QRdecomposition()
        return {
            "result": {
                "Q": [[str(x) for x in Q.row(i)] for i in range(Q.rows)],
                "R": [[str(x) for x in R.row(i)] for i in range(R.rows)]
            }
        }
    except Exception as e:
        return {"error": f"qr error: {e}"}