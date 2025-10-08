"""Core business logic for Vélib' operations."""
from __future__ import annotations
from typing import Dict, Any

from .validators import validate_station_code
from .utils import format_iso_timestamp, extract_station_data, extract_availability_data
from .fetcher import fetch_station_information, fetch_station_status
from . import db


def handle_refresh_stations() -> Dict[str, Any]:
    """Refresh static station data from API and update database.
    
    Returns:
        Dict with operation result
    """
    # Initialize database schema
    init_result = db.init_database()
    if not init_result.get("success"):
        return init_result
    
    # Fetch station information from API
    fetch_result = fetch_station_information()
    if not fetch_result.get("success"):
        return fetch_result
    
    stations_raw = fetch_result.get("data", [])
    
    if not stations_raw:
        return {
            "success": False,
            "error": "No stations received from API"
        }
    
    # Normalize station data
    stations_normalized = []
    for station in stations_raw:
        try:
            normalized = extract_station_data(station)
            stations_normalized.append(normalized)
        except Exception as e:
            # Skip malformed stations but continue
            pass
    
    if not stations_normalized:
        return {
            "success": False,
            "error": "Failed to normalize station data"
        }
    
    # Clear existing data
    clear_result = db.clear_stations_table()
    if not clear_result.get("success"):
        return clear_result
    
    # Insert new data
    insert_result = db.insert_stations(stations_normalized)
    if not insert_result.get("success"):
        return insert_result
    
    # Update metadata
    timestamp = format_iso_timestamp()
    db.update_metadata("last_refresh", timestamp, timestamp)
    db.update_metadata("station_count", str(insert_result.get("inserted_count", 0)), timestamp)
    
    return {
        "success": True,
        "operation": "refresh_stations",
        "stations_imported": insert_result.get("inserted_count", 0),
        "last_update": timestamp,
        "message": f"{insert_result.get('inserted_count', 0)} stations imported successfully"
    }


def handle_get_availability(station_code: str) -> Dict[str, Any]:
    """Get real-time availability for one station.
    
    Args:
        station_code: Station code
        
    Returns:
        Dict with availability data or error
    """
    # Validate station code
    validation = validate_station_code(station_code)
    if not validation.get("valid"):
        return {"success": False, "error": validation.get("error")}
    
    station_code = validation.get("station_code")
    
    # Fetch real-time status
    fetch_result = fetch_station_status(station_code)
    if not fetch_result.get("success"):
        return fetch_result
    
    status_raw = fetch_result.get("data")
    
    if not status_raw:
        return {
            "success": False,
            "error": f"No status data for station {station_code}"
        }
    
    # Normalize availability data
    try:
        availability = extract_availability_data(status_raw)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to parse availability data: {str(e)}"
        }
    
    return {
        "success": True,
        "operation": "get_availability",
        "station_code": availability.get("station_code"),
        "bikes": {
            "total": availability.get("num_bikes_available"),
            "mechanical": availability.get("mechanical"),
            "ebike": availability.get("ebike")
        },
        "docks_available": availability.get("num_docks_available"),
        "status": {
            "is_installed": bool(availability.get("is_installed")),
            "is_renting": bool(availability.get("is_renting")),
            "is_returning": bool(availability.get("is_returning"))
        },
        "last_reported": availability.get("last_reported"),
        "last_update_time": availability.get("last_update_time")
    }


def handle_check_cache() -> Dict[str, Any]:
    """Get cache metadata (last update, station count).
    
    Returns:
        Dict with cache info
    """
    # Initialize database if needed
    db.init_database()
    
    # Get metadata
    last_refresh = db.get_metadata("last_refresh")
    station_count_meta = db.get_metadata("station_count")
    
    # Get actual count from DB
    actual_count = db.get_station_count()
    
    result = {
        "success": True,
        "operation": "check_cache",
        "cache": {
            "last_refresh": last_refresh.get("updated_at") if last_refresh else None,
            "station_count": actual_count,
            "db_path": str(db.get_db_path())
        }
    }
    
    if last_refresh:
        result["cache"]["last_refresh_iso"] = last_refresh.get("updated_at")
    else:
        result["cache"]["message"] = "Cache is empty. Run 'refresh_stations' to populate."
    
    return result
