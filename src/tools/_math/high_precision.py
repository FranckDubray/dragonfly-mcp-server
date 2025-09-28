"""High precision mathematical operations using mpmath"""
from typing import Dict, Any

try:
    import mpmath
except ImportError:
    mpmath = None


class HighPrecisionOps:
    def handle(self, operation: str, **params) -> Dict[str, Any]:
        """Handle high precision operations."""
        if mpmath is None:
            return {"error": "mpmath not available. Install mpmath for high precision calculations."}
            
        if operation == "eval_precise":
            expr = params.get("expression") or params.get("expr")
            precision = params.get("precision", 50)
            
            if not expr:
                return {"error": "expression required"}
            
            try:
                # Set precision
                old_dps = mpmath.mp.dps
                mpmath.mp.dps = precision + 10  # Guard digits
                
                # Create context with common functions
                context = {
                    'pi': mpmath.pi,
                    'e': mpmath.e,
                    'sqrt': mpmath.sqrt,
                    'log': mpmath.log,
                    'ln': mpmath.log,
                    'sin': mpmath.sin,
                    'cos': mpmath.cos,
                    'tan': mpmath.tan,
                    'exp': mpmath.exp,
                    'power': mpmath.power,
                    'root': mpmath.root,
                    'mpmath': mpmath
                }
                
                # Evaluate expression
                result = eval(expr, {"__builtins__": {}}, context)
                
                # Format result to exact precision
                result_str = mpmath.nstr(result, precision, strip_zeros=False)
                
                # Restore precision
                mpmath.mp.dps = old_dps
                
                return {
                    "result": result_str,
                    "precision": precision,
                    "high_precision": True
                }
                
            except Exception as e:
                # Restore precision on error
                if 'old_dps' in locals():
                    mpmath.mp.dps = old_dps
                return {"error": f"High precision evaluation failed: {str(e)}"}
        
        return {"error": f"Unknown high precision operation: {operation}"}