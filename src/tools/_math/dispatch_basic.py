"""
Basic arithmetic, transcendental and complex operations for dispatcher.
These functions never raise; they return explicit error dicts on invalid input.
"""
from __future__ import annotations
from typing import Any, Dict
import math
import cmath
import statistics

from .dispatch_core import err, jsonify, get_values, get_complex


def do_add(params: Dict[str, Any], op: str):
    try:
        vals = get_values(params)
        return {"ok": True, "value": jsonify(sum(vals))}
    except Exception as e:
        return err(str(e), op)

def do_subtract(params: Dict[str, Any], op: str):
    try:
        vals = get_values(params)
        if len(vals) < 2:
            return err("subtract requires at least two values", op)
        res = vals[0]
        for v in vals[1:]:
            res -= v
        return {"ok": True, "value": jsonify(res)}
    except Exception as e:
        return err(str(e), op)

def do_multiply(params: Dict[str, Any], op: str):
    try:
        vals = get_values(params)
        res = 1.0
        for v in vals:
            res *= v
        return {"ok": True, "value": jsonify(res)}
    except Exception as e:
        return err(str(e), op)

def do_divide(params: Dict[str, Any], op: str):
    try:
        vals = get_values(params)
        if len(vals) < 2:
            return err("divide requires at least two values", op)
        res = vals[0]
        for v in vals[1:]:
            if v == 0:
                return err("Division by zero", op)
            res /= v
        return {"ok": True, "value": jsonify(res)}
    except Exception as e:
        return err(str(e), op)

def do_power(params: Dict[str, Any], op: str):
    try:
        vals = get_values(params)
        if len(vals) != 2:
            return err("power requires exactly two values (base, exponent)", op)
        try:
            return {"ok": True, "value": jsonify(math.pow(vals[0], vals[1]))}
        except Exception as e:
            return err(f"Power error: {e}", op)
    except Exception as e:
        return err(str(e), op)

def do_mod(params: Dict[str, Any], op: str):
    try:
        vals = get_values(params)
        if len(vals) != 2:
            return err("modulo requires exactly two values (a, b)", op)
        b = vals[1]
        if b == 0:
            return err("Modulo by zero", op)
        return {"ok": True, "value": jsonify(vals[0] % b)}
    except Exception as e:
        return err(str(e), op)

def do_sqrt(params: Dict[str, Any], op: str):
    try:
        vals = get_values(params)
        x = vals[0]
        use_complex = bool(params.get("complex", False))
        if x < 0 and not use_complex:
            return err("Square root of negative number: set complex=true to get complex result", op)
        return {"ok": True, "value": jsonify(math.sqrt(x) if not use_complex else cmath.sqrt(x))}
    except Exception as e:
        return err(str(e), op)

def do_trig(params: Dict[str, Any], op: str):
    try:
        vals = get_values(params)
        x = vals[0]
        deg = bool(params.get("deg") or params.get("degrees"))
        rad = math.radians(x) if deg else x
        f = getattr(math, op)
        return {"ok": True, "value": jsonify(f(rad))}
    except Exception as e:
        return err(str(e), op)

def do_ln_log(params: Dict[str, Any], op: str):
    try:
        vals = get_values(params)
        x = vals[0]
        if op == "ln":
            return {"ok": True, "value": jsonify(math.log(x))}
        base = params.get("base")
        if base is None:
            return {"ok": True, "value": jsonify(math.log10(x))}
        b = float(base)
        return {"ok": True, "value": jsonify(math.log(x, b))}
    except Exception as e:
        return err(str(e), op)

def do_exp(params: Dict[str, Any], op: str):
    try:
        vals = get_values(params)
        return {"ok": True, "value": jsonify(math.exp(vals[0]))}
    except Exception as e:
        return err(str(e), op)

def do_complex(params: Dict[str, Any], op: str):
    try:
        z = get_complex(params)
        return {"ok": True, "value": jsonify(z)}
    except Exception as e:
        return err(f"Complex parse error: {e}", op)

def do_conjugate(params: Dict[str, Any], op: str):
    try:
        z = get_complex(params)
        return {"ok": True, "value": jsonify(z.conjugate())}
    except Exception as e:
        return err(f"Conjugate error: {e}", op)

def do_magnitude(params: Dict[str, Any], op: str):
    try:
        z = get_complex(params)
        return {"ok": True, "value": jsonify(abs(z))}
    except Exception as e:
        return err(f"Magnitude error: {e}", op)

def do_phase(params: Dict[str, Any], op: str):
    try:
        z = get_complex(params)
        angle = cmath.phase(z)
        if params.get("deg") or params.get("degrees"):
            angle = math.degrees(angle)
        return {"ok": True, "value": jsonify(angle)}
    except Exception as e:
        return err(f"Phase error: {e}", op)
