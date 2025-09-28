"""Basic arithmetic with arbitrary precision"""
from decimal import Decimal, getcontext
from typing import Dict, Any

class ArithmeticOps:
    def handle(self, operation: str, **params) -> Dict[str, Any]:
        a = params.get("a")
        b = params.get("b")
        precision = params.get("precision", 28)
        if a is None or b is None:
            return {"error": "Parameters a and b required"}
        getcontext().prec = precision
        try:
            da = Decimal(str(a))
            db = Decimal(str(b))
            if operation == "add":
                result = da + db
            elif operation == "subtract":
                result = da - db
            elif operation == "multiply":
                result = da * db
            elif operation == "divide":
                if db == 0:
                    return {"error": "Division by zero"}
                result = da / db
            elif operation == "power":
                result = da ** db
            elif operation == "modulo":
                if db == 0:
                    return {"error": "Modulo by zero"}
                result = da % db
            else:
                return {"error": f"Unknown arithmetic operation: {operation}"}
            return {"result": str(result)}
        except Exception as e:
            return {"error": f"Arithmetic error: {str(e)}"}