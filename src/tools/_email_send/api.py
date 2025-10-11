"""API routing for email_send operations."""

from typing import Dict, Any
from .core import handle_test_connection, handle_send


def route_operation(operation: str, provider: str = "gmail", **params) -> Dict[str, Any]:
    """Route operation to appropriate handler.
    
    Args:
        operation: Operation name (test_connection, send)
        provider: Email provider (gmail or infomaniak)
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    handlers = {
        "test_connection": handle_test_connection,
        "send": handle_send
    }
    
    handler = handlers.get(operation)
    if not handler:
        return {
            "error": f"Unknown operation '{operation}'. Valid operations: {', '.join(handlers.keys())}"
        }
    
    return handler(provider=provider, **params)
