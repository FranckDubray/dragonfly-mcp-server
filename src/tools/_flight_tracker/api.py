"""Flight Tracker API - routing."""
from __future__ import annotations
from typing import Dict, Any

from .core import handle_track_flights


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to appropriate handler.
    
    Args:
        operation: Operation name
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    if operation == "track_flights":
        return handle_track_flights(
            latitude=params.get("latitude"),
            longitude=params.get("longitude"),
            radius_km=params.get("radius_km"),
            altitude_min=params.get("altitude_min"),
            altitude_max=params.get("altitude_max"),
            on_ground_only=params.get("on_ground_only"),
            in_flight_only=params.get("in_flight_only"),
            speed_min=params.get("speed_min"),
            speed_max=params.get("speed_max"),
            countries=params.get("countries"),
            callsign_pattern=params.get("callsign_pattern"),
            max_results=params.get("max_results", 100),
            sort_by=params.get("sort_by", "distance"),
            include_metadata=params.get("include_metadata", True)
        )
    
    return {"error": f"Unknown operation: {operation}"}
