"""Expression parser using SymPy (safe) with high precision support"""
from typing import Dict, Any

try:
    import sympy as sp
except Exception:  # SymPy may not be installed
    sp = None  # type: ignore


class ExpressionParser:
    def evaluate(self, expression: str, variables: Dict[str, Any] | None = None, precision: int | None = None) -> Dict[str, Any]:
        """Safely evaluate a mathematical expression using SymPy with high precision support.
        Returns the result with proper precision formatting.
        """
        if not expression:
            return {"error": "Empty expression"}
        if sp is None:
            return {"error": "SymPy not available. Install sympy to evaluate expressions safely."}

        try:
            vars_map = variables or {}
            symbols: Dict[str, Any] = {}
            for name in vars_map.keys():
                try:
                    symbols[name] = sp.Symbol(name)
                except Exception:
                    return {"error": f"Invalid variable name: {name}"}

            local_dict = {**symbols, "ln": sp.log, "log": sp.log, "sqrt": sp.sqrt,
                          "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
                          "pi": sp.pi, "e": sp.E, "E": sp.E, "I": sp.I, 
                          "Rational": sp.Rational, "N": sp.N}

            expr = sp.sympify(expression, locals=local_dict)

            subs_map = {}
            for k, v in vars_map.items():
                try:
                    subs_map[symbols[k]] = sp.sympify(v, locals=local_dict)
                except Exception:
                    subs_map[symbols[k]] = sp.nsimplify(v)
            expr_sub = expr.subs(subs_map)

            # Handle precision properly
            if precision and isinstance(precision, int) and precision > 1:
                # For high precision requests, use SymPy's N() with exact evaluation
                if precision <= 50:
                    # Standard precision
                    result = sp.N(expr_sub, precision)
                else:
                    # Very high precision - use mp arithmetic
                    try:
                        import mpmath
                        # Set working precision higher than requested for accuracy
                        old_dps = mpmath.mp.dps
                        mpmath.mp.dps = precision + 50  # Guard digits
                        
                        # Convert to mpmath and evaluate
                        result_mp = mpmath.neval(str(expr_sub))
                        
                        # Format with exact precision
                        result_str = mpmath.nstr(result_mp, precision, strip_zeros=False)
                        
                        # Restore precision
                        mpmath.mp.dps = old_dps
                        
                        return {"result": result_str}
                        
                    except ImportError:
                        # Fallback to SymPy high precision
                        result = sp.N(expr_sub, precision)
                        return {"result": str(result)}
            else:
                # Default precision
                try:
                    exact = sp.nsimplify(expr_sub)
                    if getattr(exact, 'is_Integer', False):
                        return {"result": str(int(exact))}
                    if getattr(exact, 'is_Rational', False) and getattr(exact, 'q', None) == 1:
                        return {"result": str(int(exact))}
                except Exception:
                    pass

                n = 28  # Default precision
                result = sp.N(expr_sub, n)

            # Format result properly
            if getattr(result, 'is_Integer', False):
                return {"result": str(int(result))}
            
            result_str = str(result)
            
            # Avoid scientific notation for reasonable-sized numbers
            if 'E' in result_str or 'e' in result_str:
                try:
                    # Try to format as decimal if reasonable
                    float_val = float(result)
                    if abs(float_val) < 1e15 and abs(float_val) > 1e-15:
                        # Format without scientific notation
                        if float_val == int(float_val):
                            return {"result": str(int(float_val))}
                        else:
                            # Remove trailing zeros
                            formatted = f"{float_val:.15f}".rstrip('0').rstrip('.')
                            return {"result": formatted}
                except:
                    pass
            
            # Clean up trailing zeros for decimal representation
            if '.' in result_str and not ('E' in result_str or 'e' in result_str):
                result_str = result_str.rstrip('0').rstrip('.')
                
            return {"result": result_str}
            
        except Exception as e:
            return {"error": f"Expression evaluation error: {str(e)}"}