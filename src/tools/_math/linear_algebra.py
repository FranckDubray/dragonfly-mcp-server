"""Linear algebra operations using SymPy matrices (base ops)"""
from __future__ import annotations
from typing import Dict, Any, List

try:
    import sympy as sp
except Exception:
    sp = None  # type: ignore


def _ensure_sympy() -> Dict[str, Any] | None:
    if sp is None:
        return {"error": "SymPy not available. Install sympy to use linear algebra operations."}
    return None


def _to_matrix(M) -> "sp.Matrix":
    if isinstance(M, sp.Matrix):
        return M
    return sp.Matrix(M)


def _to_vector(v) -> "sp.Matrix":
    if isinstance(v, sp.Matrix):
        return v
    # Handle both column and row vectors
    if isinstance(v, list) and len(v) > 0 and not isinstance(v[0], list):
        return sp.Matrix([[x] for x in v])  # Column vector
    return sp.Matrix(v)


def _matrix_to_list(M: "sp.Matrix") -> List[List[str]]:
    return [[str(x) for x in M.row(i)] for i in range(M.rows)]


def _vector_to_list(v: "sp.Matrix") -> List[str]:
    return [str(x) for x in list(v)]


class LinearAlgebraOps:
    def handle(self, operation: str, **params) -> Dict[str, Any]:
        err = _ensure_sympy()
        if err:
            return err
        op = operation
        
        try:
            if op == "mat_add":
                A = params.get("A") or params.get("a") or params.get("matrix")
                B = params.get("B") or params.get("b")
                if A is None or B is None:
                    return {"error": "Parameters A and B required for mat_add"}
                A = _to_matrix(A)
                B = _to_matrix(B)
                return {"result": _matrix_to_list(A + B)}
            
            if op == "mat_mul":
                A = params.get("A") or params.get("a") or params.get("matrix")
                B = params.get("B") or params.get("b")
                if A is None or B is None:
                    return {"error": "Parameters A and B required for mat_mul"}
                A = _to_matrix(A)
                B = _to_matrix(B)
                return {"result": _matrix_to_list(A * B)}
            
            if op == "mat_det":
                A = params.get("A") or params.get("matrix")
                if A is None:
                    return {"error": "Parameter A or matrix required for mat_det"}
                A = _to_matrix(A)
                d = A.det()
                try:
                    return {"result": float(d)}
                except Exception:
                    return {"result": str(d)}
            
            if op == "mat_inv":
                A = params.get("A") or params.get("matrix")
                if A is None:
                    return {"error": "Parameter A or matrix required for mat_inv"}
                A = _to_matrix(A)
                return {"result": _matrix_to_list(A.inv())}
            
            if op == "mat_transpose":
                A = params.get("A") or params.get("matrix")
                if A is None:
                    return {"error": "Parameter A or matrix required for mat_transpose"}
                A = _to_matrix(A)
                return {"result": _matrix_to_list(A.T)}
            
            if op == "mat_rank":
                A = params.get("A") or params.get("matrix")
                if A is None:
                    return {"error": "Parameter A or matrix required for mat_rank"}
                A = _to_matrix(A)
                return {"result": int(A.rank())}
            
            if op == "mat_solve":
                A = params.get("A") or params.get("matrix")
                b = params.get("b") or params.get("vector")
                if A is None or b is None:
                    return {"error": "Parameters A and b required for mat_solve"}
                A = _to_matrix(A)
                b = _to_vector(b)
                x = A.LUsolve(b)
                return {"result": _vector_to_list(x)}
            
            if op == "eig":
                A = params.get("A") or params.get("matrix")
                if A is None:
                    return {"error": "Parameter A or matrix required for eig"}
                A = _to_matrix(A)
                evals = [str(ev) for ev in A.eigenvals().keys()]
                evecs = []
                for val, mult, vecs in A.eigenvects():
                    for v in vecs:
                        evecs.append(_vector_to_list(v))
                return {"eigenvalues": evals, "eigenvectors": evecs}
            
            if op == "vec_add":
                v = params.get("v") or params.get("a") or params.get("vector")
                w = params.get("w") or params.get("b")
                if v is None or w is None:
                    return {"error": "Parameters v and w required for vec_add"}
                v = _to_vector(v)
                w = _to_vector(w)
                return {"result": _vector_to_list(v + w)}
            
            if op == "dot":
                v = params.get("v") or params.get("a") or params.get("vector")
                w = params.get("w") or params.get("b")
                if v is None or w is None:
                    return {"error": "Parameters v and w required for dot"}
                v = _to_vector(v)
                w = _to_vector(w)
                val = (v.T * w)[0]
                try:
                    val = float(val)
                except Exception:
                    val = str(val)
                return {"result": val}
            
            if op == "cross":
                v = params.get("v") or params.get("a") or params.get("vector")
                w = params.get("w") or params.get("b")
                if v is None or w is None:
                    return {"error": "Parameters v and w required for cross"}
                v = _to_vector(v)
                w = _to_vector(w)
                R = sp.Matrix(v).cross(sp.Matrix(w))
                return {"result": _vector_to_list(R)}
            
            if op == "norm":
                v = params.get("v") or params.get("vector")
                if v is None:
                    return {"error": "Parameter v or vector required for norm"}
                v = _to_vector(v)
                p = params.get("p", 2)
                try:
                    p = float(p)
                except Exception:
                    p = 2
                val = sp.Matrix(v).norm(p)
                try:
                    val = float(val)
                except Exception:
                    val = str(val)
                return {"result": val}
            
            return {"error": f"Unknown linear algebra operation: {operation}"}
        
        except Exception as e:
            return {"error": f"Linear algebra operation '{operation}' failed: {str(e)}"}