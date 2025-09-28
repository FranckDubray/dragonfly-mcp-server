"""
Advanced mathematical functions - transcendental, trigonometric with special cases
"""
import math
from typing import Dict, Any

# Optional high-precision backend
try:
    import mpmath as mp
except Exception:  # pragma: no cover
    mp = None

class AdvancedOps:
    def handle(self, operation: str, **params) -> Dict[str, Any]:
        value = params.get("a")
        if value is None:
            return {"error": "Parameter 'a' required"}

        # Normalize precision (accept strings like "50")
        precision_val = params.get("precision")
        precision: int | None = None
        if precision_val is not None:
            try:
                precision = int(precision_val)
            except Exception:
                precision = None

        # Optional high precision mode when user requests `precision` and mpmath is available
        wants_hp = bool(precision) and precision > 16
        if wants_hp and mp is None:
            # Explicit instead of silently falling back to double precision
            return {"error": "High precision requested (precision > 16) but mpmath is not available. Please install mpmath to enable arbitrary precision (pip install mpmath)."}
        use_hp = wants_hp and (mp is not None)

        try:
            if use_hp:
                # High precision path using mpmath
                # Guard digits to reduce rounding artifacts
                old_dps = mp.mp.dps
                mp.mp.dps = precision + 10

                # Build high-precision input (respect angle_unit for trig)
                try:
                    xa = mp.mpf(str(value))
                except Exception:
                    xa = mp.mpf(value)

                unit = (params.get("angle_unit") or "rad").lower()
                if operation in ("sin", "cos", "tan"):
                    if unit.startswith("deg"):
                        xhp = xa * (mp.pi / 180)
                    else:
                        xhp = xa

                # Compute
                if operation == "sin":
                    res = mp.sin(xhp)
                elif operation == "cos":
                    res = mp.cos(xhp)
                elif operation == "tan":
                    # If cos ~ 0 at high precision, treat as infinity with sign of sin
                    c = mp.cos(xhp)
                    if mp.almosteq(c, mp.mpf('0'), rel_eps=mp.mpf('1e-%d' % (precision//2)), abs_eps=mp.mpf('1e-%d' % (precision//2))):
                        s = mp.sign(mp.sin(xhp))
                        mp.mp.dps = old_dps
                        return {"result": "Infinity" if s >= 0 else "-Infinity"}
                    res = mp.tan(xhp)
                elif operation == "ln":
                    if xa <= 0:
                        mp.mp.dps = old_dps
                        return {"error": "Natural log undefined for non-positive values"}
                    res = mp.log(xa)
                elif operation == "log":
                    if xa <= 0:
                        mp.mp.dps = old_dps
                        return {"error": "Log undefined for non-positive values"}
                    base = params.get("b", 10)
                    try:
                        b = mp.mpf(str(base))
                    except Exception:
                        b = mp.mpf(base)
                    res = mp.log(xa, b)
                elif operation == "exp":
                    # mp.exp handles large magnitudes; return strings for infinities if it overflows
                    res = mp.exp(xa)
                elif operation == "sqrt":
                    if xa < 0:
                        mp.mp.dps = old_dps
                        return {"error": "Square root undefined for negative real values"}
                    res = mp.sqrt(xa)
                else:
                    # Fallback to standard path if op not supported here
                    mp.mp.dps = old_dps
                    return self._handle_double_precision(operation, **params)

                # Format result: fixed-point with requested decimals when reasonable
                try:
                    # Prefer fixed decimals when precision not too large
                    result_str = ("{:0.%df}" % precision).format(res)
                except Exception:
                    # Fallback to nstr with given precision (significant digits)
                    result_str = mp.nstr(res, precision, strip_zeros=False)

                mp.mp.dps = old_dps
                # Normalize edge cases
                if result_str in ("inf", "+inf"):
                    return {"result": "Infinity"}
                if result_str == "-inf":
                    return {"result": "-Infinity"}
                return {"result": result_str}

            # Default double-precision path
            return self._handle_double_precision(operation, **params)

        except ValueError as e:
            return {"error": f"Math domain error: {str(e)}"}
        except Exception as e:
            return {"error": f"Advanced math error: {str(e)}"}

    def _handle_double_precision(self, operation: str, **params) -> Dict[str, Any]:
        x = float(params.get("a"))
        if operation == "sin":
            # Check for special values where sin should be exactly 0
            if self._is_multiple_of_pi(x):
                result = 0.0
            else:
                result = math.sin(x)
                # Clean up near-zero results (more aggressive)
                if abs(result) < 1e-10:
                    result = 0.0

        elif operation == "cos":
            # Check for special values where cos should be exactly 0
            if self._is_odd_multiple_of_pi_half(x):
                result = 0.0
            else:
                result = math.cos(x)
                # Clean up near-zero results (more aggressive)
                if abs(result) < 1e-10:
                    result = 0.0

        elif operation == "tan":
            # Check for values where tan should be infinite (more tolerant)
            if self._is_odd_multiple_of_pi_half(x):
                # Determine sign based on which quadrant we're in
                pi_half_multiple = x / (math.pi / 2)
                quadrant = int(pi_half_multiple) % 4
                if quadrant in [0, 2]:  # Positive infinity zones
                    return {"result": "Infinity"}
                else:  # Negative infinity zones
                    return {"result": "-Infinity"}
            else:
                result = math.tan(x)
                # Clean up very large results that should be infinite (more aggressive)
                if abs(result) > 1e12:
                    result_str = "Infinity" if result > 0 else "-Infinity"
                    return {"result": result_str}

        elif operation == "ln":
            if x <= 0:
                return {"error": "Natural log undefined for non-positive values"}
            result = math.log(x)

        elif operation == "log":
            if x <= 0:
                return {"error": "Log undefined for non-positive values"}
            base = params.get("b", 10)
            result = math.log(x, float(base))

        elif operation == "exp":
            # Check for overflow
            if x > 700:  # e^700 is near float limit
                return {"result": "Infinity"}
            elif x < -700:
                return {"result": 0.0}
            result = math.exp(x)

        elif operation == "sqrt":
            if x < 0:
                return {"error": "Square root undefined for negative real values"}
            result = math.sqrt(x)

        else:
            return {"error": f"Unknown advanced operation: {operation}"}

        # Check if result is infinite or NaN and convert to string
        if math.isinf(result):
            return {"result": "Infinity" if result > 0 else "-Infinity"}
        elif math.isnan(result):
            return {"result": "NaN"}
        else:
            return {"result": result}

    def _is_multiple_of_pi(self, x: float) -> bool:
        """Check if x is a multiple of π (more tolerant)"""
        multiple = x / math.pi
        return abs(multiple - round(multiple)) < 1e-10
    
    def _is_odd_multiple_of_pi_half(self, x: float) -> bool:
        """Check if x is an odd multiple of π/2 (more tolerant)"""
        multiple = x / (math.pi / 2)
        rounded = round(multiple)
        return abs(multiple - rounded) < 1e-10 and rounded % 2 != 0
