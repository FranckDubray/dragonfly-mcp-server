"""API layer for pdf_download tool - input parsing and routing."""
from __future__ import annotations
from typing import Dict, Any

from .core import handle_download


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to appropriate handler.
    
    Args:
        operation: Operation to perform
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    if operation == "download":
        return handle_download(
            url=params.get("url"),
            filename=params.get("filename"),
            overwrite=params.get("overwrite", False),
            timeout=params.get("timeout", 60)
        )
    
    return {"error": f"Unknown operation: {operation}"}
