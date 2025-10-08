"""
Core helpers and error utilities for math dispatcher.
All helpers are pure and must not raise in normal flows; conversion helpers may raise
but are wrapped by caller functions to return explicit error dicts.
"""
from __future__ import annotations
from typing import Any, Dict, List


def err(msg: str, op: str) -> Dict[str, Any]:
    return {"error": msg, "operation": op}


def jsonify(val: Any) -> Any:
    """Convert values to JSON-safe structures.
    - complex -> {re, im}
    - others returned as-is (Safe JSON layer will sanitize NaN/Infinity)
    """
    if isinstance(val, complex):
        return {"re": val.real, "im": val.imag}
    return val


def as_float(x: Any) -> float:
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        return float(x.strip())
    raise TypeError(f"Cannot convert {type(x).__name__} to float")


def as_complex(x: Any) -> complex:
    if isinstance(x, complex):
        return x
    if isinstance(x, (int, float)):
        return complex(x, 0.0)
    if isinstance(x, dict):
        r = x.get("real", x.get("re", 0.0))
        i = x.get("imag", x.get("im", 0.0))
        return complex(as_float(r), as_float(i))
    if isinstance(x, (list, tuple)) and len(x) == 2:
        return complex(as_float(x[0]), as_float(x[1]))
    if isinstance(x, str):
        try:
            return complex(x.replace("i", "j"))
        except Exception:
            pass
    raise TypeError("Cannot convert value to complex")


def get_values(params: Dict[str, Any]) -> List[float]:
    for key in ("values", "numbers", "nums", "list"):
        if key in params and isinstance(params[key], (list, tuple)):
            return [as_float(v) for v in params[key]]
    if "a" in params and "b" in params:
        return [as_float(params["a"]), as_float(params["b"]) ]
    if "x" in params:
        x = params["x"]
        if isinstance(x, (list, tuple)):
            return [as_float(v) for v in x]
        return [as_float(x)]
    raise ValueError("Missing numeric inputs. Provide values[], or a+b, or x.")


def get_complex(params: Dict[str, Any]) -> complex:
    if "z" in params:
        return as_complex(params["z"])
    if any(k in params for k in ("real", "imag", "re", "im")):
        r = params.get("real", params.get("re", 0.0))
        i = params.get("imag", params.get("im", 0.0))
        return complex(as_float(r), as_float(i))
    if params.get("from_ab_as_complex") and "a" in params and "b" in params:
        return complex(as_float(params["a"]), as_float(params["b"]))
    raise ValueError("Missing complex input: provide z or real/imag or re/im")
