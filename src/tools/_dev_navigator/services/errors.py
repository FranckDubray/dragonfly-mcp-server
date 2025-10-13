from typing import Any, Dict, List

def make_error(code: str, message: str, scope: str = "tool", recoverable: bool = True) -> Dict[str, Any]:
    return {"code": code, "message": message, "scope": scope, "recoverable": recoverable}


def error_response(operation: str, code: str, message: str, scope: str = "tool", recoverable: bool = True) -> Dict[str, Any]:
    return {
        "operation": operation,
        "errors": [make_error(code, message, scope, recoverable)],
        "returned_count": 0,
        "total_count": 0,
        "truncated": False,
    }
