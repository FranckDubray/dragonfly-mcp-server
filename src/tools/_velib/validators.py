"""Input validation for Vélib' operations."""
from __future__ import annotations
from typing import Dict, Any


def validate_station_code(station_code: str) -> Dict[str, Any]:
    """Validate station code format.
    
    Args:
        station_code: Station code to validate
        
    Returns:
        Dict with 'valid' (bool) and optional 'error' (str)
    """
    if not station_code or not isinstance(station_code, str):
        return {"valid": False, "error": "station_code must be a non-empty string"}
    
    # Trim whitespace
    station_code = station_code.strip()
    
    if not station_code:
        return {"valid": False, "error": "station_code cannot be empty"}
    
    # Check length (Vélib codes are typically 5-6 digits)
    if len(station_code) > 20:
        return {"valid": False, "error": "station_code too long (max 20 chars)"}
    
    # Allow alphanumeric and dash/underscore
    if not all(c.isalnum() or c in '-_' for c in station_code):
        return {"valid": False, "error": "station_code must be alphanumeric (dash/underscore allowed)"}
    
    return {"valid": True, "station_code": station_code}
