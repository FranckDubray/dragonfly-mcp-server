from typing import Any, Dict

from ..services.errors import error_response

SUPPORTED = {"symbol_info", "find_callers", "find_callees", "find_references", "call_patterns"}

def run(p: Dict[str, Any]) -> Dict[str, Any]:
    op = p["operation"]
    if op not in SUPPORTED:
        return error_response(op, "invalid_parameters", f"Unsupported index op: {op}")
    # Placeholder empty result until reader is implemented
    return {
        "operation": op,
        "data": [],
        "returned_count": 0,
        "total_count": 0,
        "truncated": False,
        "stats": {}
    }
