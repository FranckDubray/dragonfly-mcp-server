"""
Core logic for aviation weather operations.
"""
import logging
from .services.openmeteo import get_winds_aloft as fetch_winds
from .utils import (
    get_nearest_pressure_level,
    calculate_tas as calc_tas,
    meters_to_feet,
    kmh_to_knots
)

logger = logging.getLogger(__name__)

def get_winds_aloft(latitude, longitude, altitude_m=11000):
    """
    Get wind and temperature data at altitude.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        altitude_m: Altitude in meters (default 11000m ~ FL360)
        
    Returns:
        dict: Weather data with wind speed, direction, temperature
    """
    logger.info(f"get_winds_aloft: lat={latitude}, lon={longitude}, alt={altitude_m}m")
    
    # Convert altitude to pressure level
    pressure_level_hpa = get_nearest_pressure_level(altitude_m)
    
    # Fetch data from Open-Meteo
    result = fetch_winds(latitude, longitude, pressure_level_hpa)
    
    if 'error' in result:
        logger.warning(f"get_winds_aloft failed: {result['error']}")
        return result
    
    # Enrich response with conversions
    wind_speed_kmh = result.get('wind_speed_kmh')
    
    response = {
        'success': True,
        'location': {
            'latitude': round(latitude, 4),
            'longitude': round(longitude, 4)
        },
        'altitude': {
            'meters': altitude_m,
            'feet': meters_to_feet(altitude_m),
            'flight_level': round(meters_to_feet(altitude_m) / 100),
            'pressure_level_hpa': pressure_level_hpa
        },
        'wind': {
            'speed_kmh': wind_speed_kmh,
            'speed_kts': kmh_to_knots(wind_speed_kmh) if wind_speed_kmh is not None else None,
            'direction': result.get('wind_direction'),
            'direction_name': get_wind_direction_name(result.get('wind_direction'))
        },
        'temperature': {
            'celsius': result.get('temperature_c'),
            'fahrenheit': celsius_to_fahrenheit(result.get('temperature_c'))
        },
        'timestamp': result.get('timestamp'),
        'timezone': result.get('timezone'),
        'source': result.get('source')
    }
    
    logger.info(f"get_winds_aloft success: wind {wind_speed_kmh} km/h @ FL{response['altitude']['flight_level']}")
    return response

def calculate_tas(latitude, longitude, ground_speed_kmh, heading, altitude_m=11000):
    """
    Calculate True Airspeed from ground speed and wind data.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        ground_speed_kmh: Ground speed in km/h
        heading: Aircraft heading in degrees
        altitude_m: Altitude in meters (default 11000m)
        
    Returns:
        dict: TAS calculation results
    """
    logger.info(f"calculate_tas: lat={latitude}, lon={longitude}, gs={ground_speed_kmh}, hdg={heading}, alt={altitude_m}m")
    
    # First get wind data
    winds = get_winds_aloft(latitude, longitude, altitude_m)
    
    if 'error' in winds:
        return winds
    
    # Extract wind data
    wind_speed_kmh = winds['wind']['speed_kmh']
    wind_direction = winds['wind']['direction']
    
    if wind_speed_kmh is None or wind_direction is None:
        logger.warning("calculate_tas: Wind data not available")
        return {"error": "Wind data not available for this location/altitude"}
    
    # Calculate TAS
    tas_result = calc_tas(ground_speed_kmh, heading, wind_speed_kmh, wind_direction)
    
    # Build response
    response = {
        'success': True,
        'location': winds['location'],
        'altitude': winds['altitude'],
        'aircraft': {
            'ground_speed_kmh': ground_speed_kmh,
            'ground_speed_kts': kmh_to_knots(ground_speed_kmh),
            'heading': heading,
            'true_airspeed_kmh': tas_result['tas_kmh'],
            'true_airspeed_kts': kmh_to_knots(tas_result['tas_kmh'])
        },
        'wind': winds['wind'],
        'wind_components': {
            'headwind_kmh': tas_result['wind_component_headwind'],
            'headwind_kts': kmh_to_knots(abs(tas_result['wind_component_headwind'])),
            'crosswind_kmh': tas_result['wind_component_crosswind'],
            'crosswind_kts': kmh_to_knots(abs(tas_result['wind_component_crosswind'])),
            'effect': tas_result['wind_effect']
        },
        'temperature': winds['temperature'],
        'timestamp': winds['timestamp'],
        'source': winds['source']
    }
    
    logger.info(f"calculate_tas success: TAS={tas_result['tas_kmh']} km/h, {tas_result['wind_effect']}")
    return response

def get_wind_direction_name(direction):
    """Convert wind direction in degrees to cardinal direction name."""
    if direction is None:
        return None
    
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    index = round(direction / 22.5) % 16
    return directions[index]

def celsius_to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit."""
    if celsius is None:
        return None
    return round(celsius * 9/5 + 32, 1)
