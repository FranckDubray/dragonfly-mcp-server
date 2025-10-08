"""Flight Tracker - Real-time aircraft tracking using OpenSky Network API.

Track aircraft in real-time with filters: position, radius, altitude, speed, country.
Get live position, speed, heading, vertical rate, and flight phase analysis.

Example:
    {
        "tool": "flight_tracker",
        "params": {
            "operation": "track_flights",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "radius_km": 50,
            "altitude_min": 1000,
            "altitude_max": 5000,
            "in_flight_only": true
        }
    }
"""
from __future__ import annotations
from typing import Dict, Any

from ._flight_tracker.api import route_operation
from ._flight_tracker import spec as _spec


def run(operation: str = "track_flights", **params) -> Dict[str, Any]:
    """Execute flight tracker operation.
    
    Args:
        operation: Operation to perform (track_flights)
        **params: Operation parameters
        
    Returns:
        Flight tracking results
    """
    op = (operation or params.get("operation") or "track_flights").strip().lower()
    
    # Validate required params
    if op == "track_flights":
        if not params.get("latitude") and params.get("latitude") != 0:
            return {"error": "Parameter 'latitude' is required"}
        if not params.get("longitude") and params.get("longitude") != 0:
            return {"error": "Parameter 'longitude' is required"}
        if not params.get("radius_km"):
            return {"error": "Parameter 'radius_km' is required"}
    
    return route_operation(op, **params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    return _spec()
