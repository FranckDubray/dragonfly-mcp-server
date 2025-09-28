"""Number Theory operations - primes, factorization, etc."""
from __future__ import annotations
from typing import Dict, Any, List

try:
    import sympy as sp
    from sympy import isprime, nextprime, prevprime, primefactors, factorint, totient
except ImportError:
    sp = None


def _ensure_sympy() -> Dict[str, Any] | None:
    if sp is None:
        return {"error": "SymPy not available. Install sympy to use number theory operations."}
    return None


class NumberTheoryOps:
    def handle(self, operation: str, **params) -> Dict[str, Any]:
        """Handle number theory operations."""
        err = _ensure_sympy()
        if err:
            return err
            
        try:
            if operation == "nth_prime":
                n = params.get("n")
                if n is None:
                    return {"error": "Parameter 'n' required for nth_prime"}
                n = int(n)
                if n <= 0:
                    return {"error": "n must be positive"}
                if n > 1000000:  # Limite raisonnable pour éviter les calculs trop longs
                    return {"error": "n too large (max 1,000,000), use prime_approx for estimates"}
                
                # Méthode efficace : générer jusqu'au n-ième
                p = 2
                count = 1
                if n == 1:
                    return {"result": 2}
                
                while count < n:
                    p = nextprime(p)
                    count += 1
                
                return {"result": int(p)}
            
            elif operation == "prime_approx":
                n = params.get("n")
                if n is None:
                    return {"error": "Parameter 'n' required for prime_approx"}
                n = int(n)
                if n <= 0:
                    return {"error": "n must be positive"}
                
                # Approximation du n-ième nombre premier
                import math
                if n < 6:
                    primes = [2, 3, 5, 7, 11]
                    return {"result": primes[n-1]}
                
                log_n = math.log(n)
                log_log_n = math.log(log_n)
                
                # Approximation de haute précision
                approx = n * (log_n - 1 + (log_log_n - 1)/log_n)
                
                return {
                    "result": int(approx),
                    "approximation": True,
                    "formula": "n * (ln(n) - 1 + (ln(ln(n)) - 1)/ln(n))"
                }
            
            elif operation == "is_prime":
                n = params.get("n")
                if n is None:
                    return {"error": "Parameter 'n' required for is_prime"}
                n = int(n)
                return {"result": bool(isprime(n))}
            
            elif operation == "next_prime":
                n = params.get("n")
                if n is None:
                    return {"error": "Parameter 'n' required for next_prime"}
                n = int(n)
                return {"result": int(nextprime(n))}
            
            elif operation == "prev_prime":
                n = params.get("n")
                if n is None:
                    return {"error": "Parameter 'n' required for prev_prime"}
                n = int(n)
                if n <= 2:
                    return {"error": "No prime before 2"}
                return {"result": int(prevprime(n))}
            
            elif operation == "prime_factors":
                n = params.get("n")
                if n is None:
                    return {"error": "Parameter 'n' required for prime_factors"}
                n = int(n)
                if n <= 0:
                    return {"error": "n must be positive"}
                
                factors = primefactors(n)
                return {"result": [int(f) for f in factors]}
            
            elif operation == "factorize":
                n = params.get("n")
                if n is None:
                    return {"error": "Parameter 'n' required for factorize"}
                n = int(n)
                if n <= 0:
                    return {"error": "n must be positive"}
                
                factors = factorint(n)
                return {"result": {int(p): int(e) for p, e in factors.items()}}
            
            elif operation == "euler_phi":
                n = params.get("n")
                if n is None:
                    return {"error": "Parameter 'n' required for euler_phi"}
                n = int(n)
                if n <= 0:
                    return {"error": "n must be positive"}
                
                return {"result": int(totient(n))}
            
            elif operation == "primes_range":
                start = params.get("start", 2)
                end = params.get("end")
                if end is None:
                    return {"error": "Parameter 'end' required for primes_range"}
                start, end = int(start), int(end)
                
                if end - start > 10000:
                    return {"error": "Range too large (max 10,000 numbers)"}
                
                primes = []
                p = start if start >= 2 else 2
                while p <= end:
                    if isprime(p):
                        primes.append(p)
                    p = nextprime(p)
                    if p > end:
                        break
                
                return {"result": primes[:1000]}  # Limite à 1000 résultats
            
            else:
                return {"error": f"Unknown number theory operation: {operation}"}
                
        except Exception as e:
            return {"error": f"Number theory operation '{operation}' failed: {str(e)}"}