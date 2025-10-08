"""Pure utility functions for Vélib' tool."""
from __future__ import annotations
from typing import Any, Optional
import json


def safe_json_parse(str) -> Optional[Any]:
    """Safely parse JSON string.
    
    Args:
        JSON string to parse
        
    Returns:
        Parsed data or None on error
    """
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None


def format_iso_timestamp() -> str:
    """Get current timestamp in ISO 8601 format.
    
    Returns:
        ISO timestamp string (UTC)
    """
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def extract_station_data(station_obj: dict) -> dict:
    """Extract and normalize station information data.
    
    Args:
        station_obj: Raw station object from API
        
    Returns:
        Normalized station dict with only real API fields
    """
    # Priority: stationCode (user-facing) > station_code > station_id (system ID)
    station_code = (
        station_obj.get("stationCode") or
        station_obj.get("station_code") or 
        str(station_obj.get("station_id", ""))
    )
    
    return {
        "station_code": str(station_code),
        "station_id": station_obj.get("station_id"),
        "name": station_obj.get("name", ""),
        "lat": float(station_obj.get("lat", 0.0)),
        "lon": float(station_obj.get("lon", 0.0)),
        "capacity": int(station_obj.get("capacity", 0)),
        "station_opening_hours": station_obj.get("station_opening_hours")
    }


def extract_availability_data(status_obj: dict) -> dict:
    """Extract and normalize station status data.
    
    Args:
        status_obj: Raw status object from API
        
    Returns:
        Normalized availability dict
    """
    # Priority: stationCode (user-facing) > station_code > station_id (system ID)
    station_code = (
        status_obj.get("stationCode") or
        status_obj.get("station_code") or 
        str(status_obj.get("station_id", ""))
    )
    
    # Total bikes available
    num_bikes = int(status_obj.get("num_bikes_available", 0))
    
    # Try to get bike types breakdown
    bike_types = status_obj.get("num_bikes_available_types", {})
    
    if bike_types and isinstance(bike_types, dict):
        mechanical = int(bike_types.get("mechanical", 0))
        ebike = int(bike_types.get("ebike", 0))
    else:
        # Fallback: try direct fields
        ebike = int(status_obj.get("num_ebikes_available", status_obj.get("ebike", 0)))
        mechanical = int(status_obj.get("num_mechanical_available", status_obj.get("mechanical", num_bikes - ebike)))
    
    return {
        "station_code": str(station_code),
        "num_bikes_available": num_bikes,
        "mechanical": mechanical,
        "ebike": ebike,
        "num_docks_available": int(status_obj.get("num_docks_available", 0)),
        "is_installed": int(status_obj.get("is_installed", 0)),
        "is_renting": int(status_obj.get("is_renting", 0)),
        "is_returning": int(status_obj.get("is_returning", 0)),
        "last_reported": status_obj.get("last_reported"),
        "last_update_time": status_obj.get("last_update_time", "")
    }
