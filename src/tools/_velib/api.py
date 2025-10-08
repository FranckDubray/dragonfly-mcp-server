"""API routing layer for Vélib' operations."""
from __future__ import annotations
from typing import Dict, Any

from .core import (
    handle_refresh_stations,
    handle_get_availability,
    handle_check_cache
)


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to appropriate handler.
    
    Args:
        operation: Operation name (normalized lowercase)
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    if operation == "refresh_stations":
        return handle_refresh_stations()
    
    elif operation == "get_availability":
        station_code = params.get("station_code")
        return handle_get_availability(station_code)
    
    elif operation == "check_cache":
        return handle_check_cache()
    
    else:
        return {"error": f"Unknown operation: {operation}"}
