"""API routing for video transcription operations."""
from __future__ import annotations
from typing import Dict, Any

from .core import handle_get_info, handle_transcribe


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """
    Route operation to appropriate handler.
    
    Args:
        operation: Operation name (transcribe, get_info)
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    if operation == "get_info":
        return handle_get_info(
            path=params.get("path")
        )
    
    elif operation == "transcribe":
        return handle_transcribe(
            path=params.get("path"),
            time_start=params.get("time_start", 0),
            time_end=params.get("time_end"),
            chunk_duration=params.get("chunk_duration", 60)
        )
    
    else:
        return {"error": f"Unknown operation: {operation}"}
