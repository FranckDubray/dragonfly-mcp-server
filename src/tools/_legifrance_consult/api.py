"""API Routing."""
from typing import Dict, Any
from .core import execute_ssh
from .validators import validate_operation

def route_request(operation: str, **params) -> Dict[str, Any]:
    val = validate_operation(operation)
    if not val["valid"]:
        return {"error": val["error"]}
        
    return execute_ssh(operation, **params)
