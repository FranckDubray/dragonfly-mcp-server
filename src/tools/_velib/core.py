"""Core business logic for Vélib' operations."""
from __future__ import annotations
from typing import Dict, Any
import logging

from .validators import validate_station_code
from .utils import format_iso_timestamp, extract_station_data, extract_availability_data
from .fetcher import fetch_station_information, fetch_station_status
from . import db

logger = logging.getLogger(__name__)


def handle_refresh_stations() -> Dict[str, Any]:
    """Refresh static station data from API and update database.
    
    Returns:
        Dict with operation result
    """
    logger.info("Starting station data refresh from Open Data API")
    
    # Initialize database schema
    init_result = db.init_database()
    if not init_result.get("success"):
        logger.error(f"Database initialization failed: {init_result.get('error')}")
        return {"error": init_result.get("error")}
    
    # Fetch station information from API
    fetch_result = fetch_station_information()
    if not fetch_result.get("success"):
        logger.error(f"API fetch failed: {fetch_result.get('error')}")
        return {"error": fetch_result.get("error")}
    
    stations_raw = fetch_result.get("data", [])
    
    if not stations_raw:
        logger.error("No stations received from API")
        return {"error": "No stations received from API"}
    
    logger.info(f"Received {len(stations_raw)} stations from API")
    
    # Normalize station data
    stations_normalized = []
    errors_count = 0
    for station in stations_raw:
        try:
            normalized = extract_station_data(station)
            stations_normalized.append(normalized)
        except Exception as e:
            errors_count += 1
    
    if errors_count > 0:
        logger.warning(f"Failed to normalize {errors_count} stations (skipped)")
    
    if not stations_normalized:
        logger.error("Failed to normalize any station data")
        return {"error": "Failed to normalize station data"}
    
    # Clear existing data
    clear_result = db.clear_stations_table()
    if not clear_result.get("success"):
        logger.error(f"Failed to clear stations table: {clear_result.get('error')}")
        return {"error": clear_result.get("error")}
    
    # Insert new data
    insert_result = db.insert_stations(stations_normalized)
    if not insert_result.get("success"):
        logger.error(f"Failed to insert stations: {insert_result.get('error')}")
        return {"error": insert_result.get("error")}
    
    inserted_count = insert_result.get("inserted_count", 0)
    
    # Update metadata
    timestamp = format_iso_timestamp()
    db.update_metadata("last_refresh", timestamp, timestamp)
    db.update_metadata("station_count", str(inserted_count), timestamp)
    
    logger.info(f"Successfully imported {inserted_count} stations")
    
    # Truncation warning if > 1000 stations
    result = {
        "stations_imported": inserted_count,
        "last_update": timestamp
    }
    
    if inserted_count > 1000:
        logger.warning(f"Large dataset imported: {inserted_count} stations")
        result["truncated"] = False
        result["message"] = f"{inserted_count} stations imported successfully (full dataset)"
    
    return result


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
        logger.warning(f"Invalid station_code: {validation.get('error')}")
        return {"error": validation.get("error")}
    
    station_code = validation.get("station_code")
    
    logger.info(f"Fetching availability for station {station_code}")
    
    # Fetch real-time status
    fetch_result = fetch_station_status(station_code)
    if not fetch_result.get("success"):
        logger.error(f"Failed to fetch status for {station_code}: {fetch_result.get('error')}")
        return {"error": fetch_result.get("error")}
    
    status_raw = fetch_result.get("data")
    
    if not status_raw:
        logger.error(f"No status data for station {station_code}")
        return {"error": f"No status data for station {station_code}"}
    
    # Normalize availability data
    try:
        availability = extract_availability_data(status_raw)
    except Exception as e:
        logger.error(f"Failed to parse availability data: {str(e)}")
        return {"error": f"Failed to parse availability {str(e)}"}
    
    logger.info(f"Station {station_code}: {availability.get('num_bikes_available')} bikes, {availability.get('num_docks_available')} docks")
    
    return {
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
    logger.info("Checking cache metadata")
    
    # Initialize database if needed
    db.init_database()
    
    # Get metadata
    last_refresh = db.get_metadata("last_refresh")
    station_count_meta = db.get_metadata("station_count")
    
    # Get actual count from DB
    actual_count = db.get_station_count()
    
    logger.info(f"Cache contains {actual_count} stations, last refresh: {last_refresh.get('updated_at') if last_refresh else 'never'}")
    
    result = {
        "cache": {
            "last_refresh": last_refresh.get("updated_at") if last_refresh else None,
            "station_count": actual_count,
            "db_path": str(db.get_db_path())
        }
    }
    
    if not last_refresh:
        result["cache"]["message"] = "Cache is empty. Run 'refresh_stations' to populate."
        logger.warning("Cache is empty")
    
    return result
