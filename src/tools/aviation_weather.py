"""
Aviation Weather Tool - Upper air weather data via Open-Meteo API.

Provides wind speed, direction, and temperature at flight altitudes.
Useful for flight planning and explaining aircraft performance (TAS calculation).

Operations:
- get_winds_aloft: Get wind and temperature at specific altitude/coordinates
- calculate_tas: Calculate True Airspeed from ground speed and wind

Examples:
    # Get winds at FL360 near Paris
    {"operation": "get_winds_aloft", "latitude": 48.86, "longitude": 2.35, "altitude_m": 11000}
    
    # Calculate TAS for aircraft
    {"operation": "calculate_tas", "latitude": 48.59, "longitude": 6.27, 
     "ground_speed_kmh": 978, "heading": 127, "altitude_m": 11278}
"""
from ._aviation_weather.api import route_operation
from ._aviation_weather import spec as _spec

def run(operation=None, latitude=None, longitude=None, altitude_m=None,
        ground_speed_kmh=None, heading=None, **params):
    """
    Execute aviation weather operation.
    
    Args:
        operation: Operation to perform (get_winds_aloft or calculate_tas)
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        altitude_m: Altitude in meters (optional, default 11000m ~ FL360)
        ground_speed_kmh: Ground speed for TAS calculation (optional)
        heading: Heading for TAS calculation (optional)
        
    Returns:
        dict: Operation result
    """
    # Default operation
    if operation is None:
        operation = 'get_winds_aloft'
    
    operation = operation.strip().lower()
    
    # Validate required parameters
    if latitude is None or longitude is None:
        return {"error": "Parameters 'latitude' and 'longitude' are required"}
    
    return route_operation(
        operation=operation,
        latitude=latitude,
        longitude=longitude,
        altitude_m=altitude_m,
        ground_speed_kmh=ground_speed_kmh,
        heading=heading
    )

def spec():
    """Return tool specification."""
    return _spec()
