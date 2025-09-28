"""Complex number operations (minimal outputs)"""
import cmath
from typing import Dict, Any

class ComplexOps:
    def handle(self, operation: str, **params) -> Dict[str, Any]:
        if operation == "complex":
            # DEBUG: Let's see what we receive
            print(f"DEBUG complex_ops: operation={operation}, params={params}")
            
            # Accept both (real, imag) and (a, b) parameter naming
            real = params.get("real") or params.get("a", 0)
            imag = params.get("imag") or params.get("b", 0)
            
            print(f"DEBUG complex_ops: real={real}, imag={imag}")
            
            try:
                z = complex(float(real), float(imag))
                return {"result": str(z)}
            except Exception as e:
                return {"error": f"Complex creation error: {str(e)}"}

        z_input = params.get("a")
        if z_input is None:
            return {"error": "Complex number required"}
        try:
            if isinstance(z_input, str):
                z = complex(z_input.replace("i", "j"))
            else:
                z = complex(z_input)

            if operation == "conjugate":
                return {"result": str(z.conjugate())}
            if operation == "magnitude":
                return {"result": abs(z)}
            if operation == "phase":
                return {"result": cmath.phase(z)}
            return {"error": f"Unknown complex operation: {operation}"}
        except Exception as e:
            return {"error": f"Complex operation error: {str(e)}"}