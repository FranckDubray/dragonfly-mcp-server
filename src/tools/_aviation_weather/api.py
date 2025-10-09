"""
API routing for aviation weather operations.
"""
from .validators import validate_coordinates, validate_altitude, validate_tas_params
from .core import get_winds_aloft, calculate_tas

def route_operation(operation, latitude, longitude, altitude_m=None, 
                   ground_speed_kmh=None, heading=None):
    """
    Route request to appropriate handler.
    
    Args:
        operation: Operation name
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        altitude_m: Altitude in meters (optional, default 11000)
        ground_speed_kmh: Ground speed for TAS calculation (optional)
        heading: Heading for TAS calculation (optional)
        
    Returns:
        dict: Operation result or error
    """
    # Validate coordinates
    coord_error = validate_coordinates(latitude, longitude)
    if coord_error:
        return coord_error
    
    # Validate altitude
    alt_error = validate_altitude(altitude_m)
    if alt_error:
        return alt_error
    
    # Set default altitude if not provided
    if altitude_m is None:
        altitude_m = 11000
    
    # Route to handler
    if operation == 'get_winds_aloft':
        return get_winds_aloft(latitude, longitude, altitude_m)
    
    elif operation == 'calculate_tas':
        # Validate TAS-specific parameters
        tas_error = validate_tas_params(ground_speed_kmh, heading)
        if tas_error:
            return tas_error
        
        return calculate_tas(latitude, longitude, ground_speed_kmh, heading, altitude_m)
    
    else:
        return {"error": f"Unknown operation: {operation}"}
