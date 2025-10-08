"""API routing for YouTube download operations."""
from __future__ import annotations
from typing import Dict, Any

from .core import handle_get_info, handle_download


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to appropriate handler.
    
    Args:
        operation: Operation to perform
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    operation = operation.strip().lower()
    
    if operation == "get_info":
        return handle_get_info(
            url=params.get("url"),
            timeout=params.get("timeout"),
        )
    
    elif operation == "download":
        return handle_download(
            url=params.get("url"),
            media_type=params.get("media_type"),
            quality=params.get("quality"),
            filename=params.get("filename"),
            max_duration=params.get("max_duration"),
            timeout=params.get("timeout"),
        )
    
    else:
        return {"error": f"Unknown operation: {operation}"}
