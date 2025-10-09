"""API routing for youtube_search operations."""

from typing import Dict, Any
from .core import handle_search, handle_get_video_details, handle_get_trending


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to appropriate handler.
    
    Args:
        operation: Operation name
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    handlers = {
        "search": handle_search,
        "get_video_details": handle_get_video_details,
        "get_trending": handle_get_trending
    }
    
    handler = handlers.get(operation)
    if not handler:
        return {
            "error": f"Unknown operation: {operation}",
            "available_operations": list(handlers.keys())
        }
    
    return handler(**params)
