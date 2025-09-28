"""Math Tool - Thin entry file (delegates to dispatcher)"""
from typing import Dict, Any
from pathlib import Path
import json

try:
    from ._math import dispatcher as D
except ImportError:
    D = None

_SPEC_DIR = Path(__file__).resolve().parent.parent / "tool_specs"


def _load_spec_override(name: str) -> Dict[str, Any] | None:
    try:
        p = _SPEC_DIR / f"{name}.json"
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def run(operation: str = None, **params) -> Dict[str, Any]:
    """Run math operation with comprehensive error handling."""
    
    # Check if dispatcher is available
    if D is None:
        return {
            "error": "Math dispatcher module not available. Please check the installation.",
            "details": "The _math.dispatcher module could not be imported."
        }
    
    # Validate operation parameter
    if operation is None:
        return {
            "error": "Missing required parameter 'operation'",
            "help": "Specify an operation like 'add', 'subtract', 'multiply', etc.",
            "available_operations": [
                "add", "subtract", "multiply", "divide", "power", "modulo",
                "sin", "cos", "tan", "ln", "log", "exp", "sqrt",
                "complex", "conjugate", "magnitude", "phase",
                "mean", "median", "mode", "stdev", "variance",
                "mat_add", "mat_mul", "mat_det", "mat_inv",
                "solve_eq", "derivative", "integral", "simplify",
                "and many more..."
            ]
        }
    
    if not isinstance(operation, str):
        return {
            "error": f"Parameter 'operation' must be a string, got {type(operation).__name__}",
            "received": str(operation)
        }
    
    if not operation.strip():
        return {
            "error": "Parameter 'operation' cannot be empty",
            "help": "Provide a valid operation name like 'add', 'multiply', etc."
        }
    
    try:
        # Delegate to dispatcher - return directly without double wrapping
        result = D.handle(operation, **params)
        
        # If it's an error dict, add operation context
        if isinstance(result, dict) and "error" in result:
            result["operation"] = operation
            
        return result
            
    except Exception as e:
        return {
            "error": f"Math operation '{operation}' failed with unexpected error: {str(e)}",
            "operation": operation,
            "type": type(e).__name__
        }


def spec() -> Dict[str, Any]:
    base = {
        "type": "function",
        "function": {
            "name": "math",
            "displayName": "Math",
            "description": "Maths: arithmétique (précision arbitr.), expressions (SymPy), symbolique, complexes, probas (suppl.), algèbre linéaire (+ext), solveurs, calcul diff., stats, sommes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string"}
                },
                "required": ["operation"],
                "additionalProperties": True
            }
        }
    }
    override = _load_spec_override("math")
    if override and isinstance(override, dict):
        # Merge only displayName/description/parameters if provided
        fn = base.get("function", {})
        ofn = override.get("function", {})
        if ofn.get("displayName"):
            fn["displayName"] = ofn["displayName"]
        if ofn.get("description"):
            fn["description"] = ofn["description"]
        if ofn.get("parameters"):
            fn["parameters"] = ofn["parameters"]
    return base