"""
Input validation for aviation weather tool.
"""

def validate_coordinates(latitude, longitude):
    """
    Validate latitude and longitude.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        dict: Error dict if invalid, None if valid
    """
    if latitude is None or longitude is None:
        return {"error": "Both latitude and longitude are required"}
    
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return {"error": "Latitude and longitude must be numbers"}
    
    if not -90 <= latitude <= 90:
        return {"error": f"Latitude must be between -90 and 90 (got {latitude})"}
    
    if not -180 <= longitude <= 180:
        return {"error": f"Longitude must be between -180 and 180 (got {longitude})"}
    
    return None

def validate_altitude(altitude_m):
    """
    Validate altitude parameter.
    
    Args:
        altitude_m: Altitude in meters
        
    Returns:
        dict: Error dict if invalid, None if valid
    """
    if altitude_m is None:
        return None  # Optional parameter
    
    if not isinstance(altitude_m, (int, float)):
        return {"error": "Altitude must be a number"}
    
    if not 1000 <= altitude_m <= 20000:
        return {"error": f"Altitude must be between 1000 and 20000 meters (got {altitude_m})"}
    
    return None

def validate_tas_params(ground_speed_kmh, heading):
    """
    Validate parameters for TAS calculation.
    
    Args:
        ground_speed_kmh: Ground speed in km/h
        heading: Heading in degrees
        
    Returns:
        dict: Error dict if invalid, None if valid
    """
    if ground_speed_kmh is None:
        return {"error": "Parameter 'ground_speed_kmh' is required for calculate_tas operation"}
    
    if heading is None:
        return {"error": "Parameter 'heading' is required for calculate_tas operation"}
    
    if not isinstance(ground_speed_kmh, (int, float)):
        return {"error": "Ground speed must be a number"}
    
    if ground_speed_kmh < 0:
        return {"error": f"Ground speed cannot be negative (got {ground_speed_kmh})"}
    
    if not isinstance(heading, (int, float)):
        return {"error": "Heading must be a number"}
    
    if not 0 <= heading <= 360:
        return {"error": f"Heading must be between 0 and 360 degrees (got {heading})"}
    
    return None
