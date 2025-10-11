"""API routing for office_to_pdf operations."""

from typing import Dict, Any
from .core import handle_convert, handle_get_info


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to appropriate handler.
    
    Args:
        operation: Operation name (convert, get_info)
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    handlers = {
        "convert": handle_convert,
        "get_info": handle_get_info
    }
    
    handler = handlers.get(operation)
    if not handler:
        return {
            "error": f"Unknown operation '{operation}'. Valid operations: {', '.join(handlers.keys())}"
        }
    
    return handler(**params)
