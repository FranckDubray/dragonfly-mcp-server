"""Flight Tracker validators."""
from __future__ import annotations
from typing import Dict, Any, Optional


def validate_position(latitude: float, longitude: float) -> Dict[str, Any]:
    """Validate latitude/longitude.
    
    Args:
        latitude: Latitude value
        longitude: Longitude value
        
    Returns:
        Validation result
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        
        if lat < -90 or lat > 90:
            return {"valid": False, "error": "Latitude must be between -90 and 90"}
        
        if lon < -180 or lon > 180:
            return {"valid": False, "error": "Longitude must be between -180 and 180"}
        
        return {"valid": True, "latitude": lat, "longitude": lon}
    
    except (ValueError, TypeError):
        return {"valid": False, "error": "Invalid latitude/longitude values"}


def validate_radius(radius_km: float) -> Dict[str, Any]:
    """Validate radius.
    
    Args:
        radius_km: Radius in kilometers
        
    Returns:
        Validation result
    """
    try:
        radius = float(radius_km)
        
        if radius < 1:
            return {"valid": False, "error": "Radius must be at least 1 km"}
        
        if radius > 500:
            return {"valid": False, "error": "Radius cannot exceed 500 km"}
        
        return {"valid": True, "radius_km": radius}
    
    except (ValueError, TypeError):
        return {"valid": False, "error": "Invalid radius value"}


def validate_filters(
    altitude_min: Optional[float] = None,
    altitude_max: Optional[float] = None,
    speed_min: Optional[float] = None,
    speed_max: Optional[float] = None,
    on_ground_only: bool = False,
    in_flight_only: bool = False
) -> Dict[str, Any]:
    """Validate filter parameters.
    
    Args:
        altitude_min: Min altitude
        altitude_max: Max altitude
        speed_min: Min speed
        speed_max: Max speed
        on_ground_only: Ground only flag
        in_flight_only: Flight only flag
        
    Returns:
        Validation result
    """
    # Validate altitude range
    if altitude_min is not None and altitude_max is not None:
        if altitude_min > altitude_max:
            return {"valid": False, "error": "altitude_min cannot be greater than altitude_max"}
    
    # Validate speed range
    if speed_min is not None and speed_max is not None:
        if speed_min > speed_max:
            return {"valid": False, "error": "speed_min cannot be greater than speed_max"}
    
    # Validate ground filters
    if on_ground_only and in_flight_only:
        return {"valid": False, "error": "Cannot use both on_ground_only and in_flight_only"}
    
    return {"valid": True}
