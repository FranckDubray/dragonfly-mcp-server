"""
Vélib' Métropole Tool - Cache manager for Paris bike-sharing data

Manages SQLite cache of static station data and fetches real-time availability.
Complex queries should use sqlite_db tool directly (db_name: 'velib').

Operations:
  - refresh_stations: Fetch and update static station data
  - get_availability: Get real-time bike/dock availability for one station
  - check_cache: Get cache metadata (last update, station count)

Example:
  {
    "tool": "velib",
    "params": {
      "operation": "refresh_stations"
    }
  }
  
  {
    "tool": "velib",
    "params": {
      "operation": "get_availability",
      "station_code": "16107"
    }
  }
"""
from __future__ import annotations
from typing import Dict, Any

from ._velib.api import route_operation
from ._velib import spec as _spec


def run(operation: str = None, **params) -> Dict[str, Any]:
    """Execute Vélib' operation.
    
    Args:
        operation: Operation to perform (refresh_stations, get_availability, check_cache)
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    # Normalize operation
    op = (operation or params.get("operation", "")).strip().lower()
    
    if not op:
        return {"error": "operation parameter is required"}
    
    # Validate required params
    if op == "get_availability":
        if not params.get("station_code"):
            return {"error": "station_code is required for get_availability operation"}
    
    # Route to handler
    return route_operation(op, **params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    return _spec()
