"""Ship Tracker - Track ships and vessels in real-time using AIS data.

Free AIS (Automatic Identification System) data from aisstream.io
No API key required for basic usage.

Example usage:
    # Track ships near a location
    {
        "tool": "ship_tracker",
        "params": {
            "operation": "track_ships",
            "latitude": 51.9225,
            "longitude": 4.4792,
            "radius_km": 50,
            "ship_type": "cargo"
        }
    }
    
    # Get details about a specific ship
    {
        "tool": "ship_tracker",
        "params": {
            "operation": "get_ship_details",
            "mmsi": 123456789
        }
    }
    
    # Check port traffic
    {
        "tool": "ship_tracker",
        "params": {
            "operation": "get_port_traffic",
            "port_name": "Rotterdam",
            "radius_km": 20
        }
    }

Ship types supported:
    - fishing, towing, dredging, diving, military
    - sailing, pleasure, highspeed, pilot, sar
    - tug, port, pollution, law, medical
    - passenger, cargo, tanker, other

Navigation statuses:
    - underway, anchored, moored, aground, fishing, sailing
"""
from __future__ import annotations
from typing import Dict, Any

# Import from implementation package
from ._ship_tracker.api import route_operation
from ._ship_tracker import spec as _spec


def run(operation: str = "track_ships", **params) -> Dict[str, Any]:
    """Execute ship tracker operation.
    
    Args:
        operation: Operation to perform
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    # Normalize operation
    op = (operation or params.get("operation") or "track_ships").strip().lower()
    
    # Validate required params for each operation
    if op == "track_ships":
        if params.get("latitude") is None or params.get("longitude") is None:
            return {"error": "Parameters 'latitude' and 'longitude' are required for track_ships operation"}
    
    elif op == "get_ship_details":
        if not params.get("mmsi"):
            return {"error": "Parameter 'mmsi' is required for get_ship_details operation"}
    
    elif op == "get_port_traffic":
        port_name = params.get("port_name")
        lat = params.get("latitude")
        lon = params.get("longitude")
        if not port_name and (lat is None or lon is None):
            return {"error": "Either 'port_name' or both 'latitude' and 'longitude' are required for get_port_traffic operation"}
    
    # Route to handler
    return route_operation(op, **params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    return _spec()
