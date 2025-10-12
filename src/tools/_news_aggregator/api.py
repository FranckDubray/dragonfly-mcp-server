"""API routing for news aggregator operations."""
from .core import (
    handle_search_news,
    handle_top_headlines,
    handle_list_sources
)


def route_operation(operation: str, **params):
    """
    Route operation to appropriate handler.
    
    Args:
        operation: Operation name
        **params: Operation parameters
        
    Returns:
        Dict with result or error
    """
    # Operation mapping
    operations = {
        "search_news": handle_search_news,
        "top_headlines": handle_top_headlines,
        "list_sources": handle_list_sources
    }
    
    handler = operations.get(operation)
    if not handler:
        available_ops = ", ".join(sorted(operations.keys()))
        return {
            "error": f"Unknown operation '{operation}'. Available: {available_ops}"
        }
    
    try:
        return handler(**params)
    except Exception as e:
        return {
            "error": f"Handler error for '{operation}': {str(e)}",
            "operation": operation
        }
