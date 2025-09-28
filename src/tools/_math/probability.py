"""Probability and statistics operations"""
import math
import statistics
from typing import Dict, Any, List

class ProbabilityOps:
    def handle(self, operation: str, **params) -> Dict[str, Any]:
        """Handle probability and statistics operations (minimal outputs)."""
        
        if operation in ["mean", "median", "mode", "stdev", "variance"]:
            data = params.get("data")
            if not data or not isinstance(data, list):
                return {"error": "data list required"}
            try:
                if operation == "mean":
                    result = statistics.mean(data)
                elif operation == "median":
                    result = statistics.median(data)
                elif operation == "mode":
                    result = statistics.mode(data)
                elif operation == "stdev":
                    result = statistics.stdev(data) if len(data) > 1 else 0
                elif operation == "variance":
                    result = statistics.variance(data) if len(data) > 1 else 0
                return {"result": result}
            except Exception as e:
                return {"error": f"Statistics error: {str(e)}"}
        
        elif operation in ["combination", "permutation"]:
            # Support both n,r and n,k parameter naming
            n = params.get("n")
            r = params.get("r") or params.get("k")
            if n is None or r is None:
                return {"error": "n and r (or k) required"}
            try:
                n, r = int(n), int(r)
                if n < 0 or r < 0:
                    return {"error": "n and r must be non-negative"}
                if r > n:
                    return {"error": f"r ({r}) cannot be greater than n ({n})"}
                if operation == "combination":
                    result = math.comb(n, r)
                else:
                    result = math.perm(n, r)
                return {"result": result}
            except Exception as e:
                return {"error": f"Combinatorics error: {str(e)}"}
        
        elif operation == "normal_pdf":
            x = params.get("x")
            mu = params.get("mu", 0)
            sigma = params.get("sigma", 1)
            if x is None:
                return {"error": "x value required"}
            try:
                x, mu, sigma = float(x), float(mu), float(sigma)
                if sigma <= 0:
                    return {"error": "sigma must be positive"}
                result = (1 / (sigma * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - mu) / sigma) ** 2)
                return {"result": result}
            except Exception as e:
                return {"error": f"Normal PDF error: {str(e)}"}
        
        elif operation == "binomial":
            n = params.get("n")
            k = params.get("k") 
            p = params.get("p")
            if n is None or k is None or p is None:
                return {"error": "n, k, and p required"}
            try:
                n, k = int(n), int(k)
                p = float(p)
                if not (0 <= p <= 1):
                    return {"error": "p must be between 0 and 1"}
                if not (0 <= k <= n):
                    return {"error": "k must be between 0 and n"}
                result = math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
                return {"result": result}
            except Exception as e:
                return {"error": f"Binomial error: {str(e)}"}
        
        return {"error": f"Unknown probability operation: {operation}"}