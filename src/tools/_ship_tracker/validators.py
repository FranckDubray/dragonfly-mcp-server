"""Input validation for ship tracker operations."""

from typing import Dict, Any, Optional


def validate_track_ships_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate track_ships operation parameters.
    
    Args:
        params: Track ships parameters
        
    Returns:
        Validated parameters
        
    Raises:
        ValueError: If validation fails
    """
    # Validate latitude
    latitude = params.get("latitude")
    if latitude is None:
        raise ValueError("Parameter 'latitude' is required")
    if not isinstance(latitude, (int, float)):
        raise ValueError("Parameter 'latitude' must be a number")
    if not -90 <= latitude <= 90:
        raise ValueError("Parameter 'latitude' must be between -90 and 90")
    
    # Validate longitude
    longitude = params.get("longitude")
    if longitude is None:
        raise ValueError("Parameter 'longitude' is required")
    if not isinstance(longitude, (int, float)):
        raise ValueError("Parameter 'longitude' must be a number")
    if not -180 <= longitude <= 180:
        raise ValueError("Parameter 'longitude' must be between -180 and 180")
    
    # Validate radius
    radius_km = params.get("radius_km", 50)
    if not isinstance(radius_km, (int, float)):
        raise ValueError("Parameter 'radius_km' must be a number")
    if not 1 <= radius_km <= 500:
        raise ValueError("Parameter 'radius_km' must be between 1 and 500")
    
    # Validate timeout (default changed from 10 to 15)
    timeout = params.get("timeout", 15)
    if not isinstance(timeout, (int, float)):
        raise ValueError("Parameter 'timeout' must be a number")
    if not 3 <= timeout <= 60:
        raise ValueError("Parameter 'timeout' must be between 3 and 60 seconds")
    
    # Validate ship_type
    ship_type = params.get("ship_type")
    if ship_type is not None:
        valid_types = [
            "fishing", "towing", "dredging", "diving", "military",
            "sailing", "pleasure", "highspeed", "pilot", "sar",
            "tug", "port", "pollution", "law", "medical",
            "passenger", "cargo", "tanker", "other"
        ]
        if ship_type not in valid_types:
            raise ValueError(f"Parameter 'ship_type' must be one of: {', '.join(valid_types)}")
    
    # Validate min/max length
    min_length = params.get("min_length")
    if min_length is not None:
        if not isinstance(min_length, (int, float)) or min_length < 0:
            raise ValueError("Parameter 'min_length' must be a positive number")
    
    max_length = params.get("max_length")
    if max_length is not None:
        if not isinstance(max_length, (int, float)) or max_length < 0:
            raise ValueError("Parameter 'max_length' must be a positive number")
    
    # Validate min/max speed
    min_speed = params.get("min_speed_knots")
    if min_speed is not None:
        if not isinstance(min_speed, (int, float)) or min_speed < 0:
            raise ValueError("Parameter 'min_speed_knots' must be a positive number")
    
    max_speed = params.get("max_speed_knots")
    if max_speed is not None:
        if not isinstance(max_speed, (int, float)) or max_speed < 0:
            raise ValueError("Parameter 'max_speed_knots' must be a positive number")
    
    # Validate navigation_status
    nav_status = params.get("navigation_status")
    if nav_status is not None:
        valid_statuses = [
            "underway", "anchored", "moored", "aground", "fishing", "sailing"
        ]
        if nav_status not in valid_statuses:
            raise ValueError(f"Parameter 'navigation_status' must be one of: {', '.join(valid_statuses)}")
    
    # Validate max_results
    max_results = params.get("max_results", 50)
    if not isinstance(max_results, int) or not 1 <= max_results <= 200:
        raise ValueError("Parameter 'max_results' must be an integer between 1 and 200")
    
    return {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "radius_km": float(radius_km),
        "timeout": int(timeout),
        "ship_type": ship_type,
        "min_length": float(min_length) if min_length is not None else None,
        "max_length": float(max_length) if max_length is not None else None,
        "min_speed_knots": float(min_speed) if min_speed is not None else None,
        "max_speed_knots": float(max_speed) if max_speed is not None else None,
        "navigation_status": nav_status,
        "max_results": int(max_results),
        "sort_by": params.get("sort_by", "distance")
    }


def validate_ship_details_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate get_ship_details operation parameters.
    
    Args:
        params: Ship details parameters
        
    Returns:
        Validated parameters
        
    Raises:
        ValueError: If validation fails
    """
    mmsi = params.get("mmsi")
    if mmsi is None:
        raise ValueError("Parameter 'mmsi' is required")
    
    # MMSI is a 9-digit number
    if not isinstance(mmsi, (int, str)):
        raise ValueError("Parameter 'mmsi' must be a number or string")
    
    mmsi_str = str(mmsi)
    if not mmsi_str.isdigit() or len(mmsi_str) != 9:
        raise ValueError("Parameter 'mmsi' must be a 9-digit number")
    
    # Validate timeout (default changed from 10 to 30 for better detection)
    timeout = params.get("timeout", 30)
    if not isinstance(timeout, (int, float)):
        raise ValueError("Parameter 'timeout' must be a number")
    if not 3 <= timeout <= 60:
        raise ValueError("Parameter 'timeout' must be between 3 and 60 seconds")
    
    return {
        "mmsi": int(mmsi),
        "timeout": int(timeout)
    }


def validate_port_traffic_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate get_port_traffic operation parameters.
    
    Args:
        params: Port traffic parameters
        
    Returns:
        Validated parameters
        
    Raises:
        ValueError: If validation fails
    """
    # Port can be specified by name or coordinates
    port_name = params.get("port_name")
    latitude = params.get("latitude")
    longitude = params.get("longitude")
    
    # Validate timeout (default changed from 10 to 15)
    timeout = params.get("timeout", 15)
    if not isinstance(timeout, (int, float)):
        raise ValueError("Parameter 'timeout' must be a number")
    if not 3 <= timeout <= 60:
        raise ValueError("Parameter 'timeout' must be between 3 and 60 seconds")
    
    if port_name:
        return {
            "port_name": port_name.strip(),
            "radius_km": params.get("radius_km", 10),
            "timeout": int(timeout),
            "max_results": params.get("max_results", 50)
        }
    elif latitude is not None and longitude is not None:
        if not isinstance(latitude, (int, float)) or not -90 <= latitude <= 90:
            raise ValueError("Parameter 'latitude' must be between -90 and 90")
        if not isinstance(longitude, (int, float)) or not -180 <= longitude <= 180:
            raise ValueError("Parameter 'longitude' must be between -180 and 180")
        
        radius_km = params.get("radius_km", 10)
        if not isinstance(radius_km, (int, float)) or not 1 <= radius_km <= 100:
            raise ValueError("Parameter 'radius_km' must be between 1 and 100")
        
        return {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "radius_km": float(radius_km),
            "timeout": int(timeout),
            "max_results": params.get("max_results", 50)
        }
    else:
        raise ValueError("Either 'port_name' or both 'latitude' and 'longitude' must be provided")
