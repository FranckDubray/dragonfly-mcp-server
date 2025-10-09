"""
Utility functions for aviation weather calculations.
"""
import math

# Altitude to pressure level mapping (approximate)
ALTITUDE_TO_PRESSURE = {
    20000: 50,    # ~20km
    16000: 100,   # ~16km
    13500: 150,   # ~13.5km
    12000: 200,   # ~12km FL390
    11000: 225,   # ~11km FL360
    10000: 250,   # ~10km FL330
    9000: 300,    # ~9km FL300
    7500: 400,    # ~7.5km FL250
    5500: 500,    # ~5.5km FL180
    4200: 600,    # ~4.2km FL140
    3000: 700,    # ~3km FL100
    1500: 850,    # ~1.5km FL50
    1000: 925,    # ~1km
    100: 1000     # Sea level
}

def get_nearest_pressure_level(altitude_m):
    """
    Convert altitude in meters to nearest standard pressure level.
    
    Args:
        altitude_m: Altitude in meters
        
    Returns:
        int: Pressure level in hPa (e.g., 225 for FL360)
    """
    if altitude_m <= 100:
        return 1000
    
    # Find nearest altitude key
    altitudes = sorted(ALTITUDE_TO_PRESSURE.keys())
    nearest_alt = min(altitudes, key=lambda x: abs(x - altitude_m))
    return ALTITUDE_TO_PRESSURE[nearest_alt]

def calculate_wind_components(wind_speed_kmh, wind_direction):
    """
    Calculate u and v wind components.
    
    Args:
        wind_speed_kmh: Wind speed in km/h
        wind_direction: Wind direction in degrees (meteorological convention: direction FROM which wind blows)
        
    Returns:
        tuple: (u_component, v_component) in km/h
    """
    if wind_speed_kmh is None or wind_direction is None:
        return (0, 0)
    
    # Convert to radians
    direction_rad = math.radians(wind_direction)
    
    # Meteorological convention: wind FROM this direction
    # So we add 180° to get the direction TO which wind blows
    direction_rad += math.pi
    
    # Calculate components
    u = wind_speed_kmh * math.sin(direction_rad)  # East-west component (positive = eastward)
    v = wind_speed_kmh * math.cos(direction_rad)  # North-south component (positive = northward)
    
    return (u, v)

def calculate_tas(ground_speed_kmh, heading, wind_speed_kmh, wind_direction):
    """
    Calculate True Airspeed from ground speed and wind.
    
    Args:
        ground_speed_kmh: Ground speed in km/h
        heading: Aircraft heading in degrees
        wind_speed_kmh: Wind speed in km/h
        wind_direction: Wind direction in degrees (FROM which wind blows)
        
    Returns:
        dict: {
            'tas_kmh': True airspeed in km/h,
            'wind_component_headwind': Headwind component (positive = headwind, negative = tailwind),
            'wind_component_crosswind': Crosswind component (positive = from right)
        }
    """
    # Get wind components
    wind_u, wind_v = calculate_wind_components(wind_speed_kmh, wind_direction)
    
    # Aircraft velocity components
    heading_rad = math.radians(heading)
    gs_u = ground_speed_kmh * math.sin(heading_rad)
    gs_v = ground_speed_kmh * math.cos(heading_rad)
    
    # True airspeed components (remove wind)
    tas_u = gs_u - wind_u
    tas_v = gs_v - wind_v
    
    # Calculate TAS magnitude
    tas_kmh = math.sqrt(tas_u**2 + tas_v**2)
    
    # Calculate wind components relative to aircraft heading
    # Wind component along flight path (positive = tailwind, negative = headwind in aviation convention)
    # Crosswind: wind component perpendicular to flight path (positive = from right)
    along_track = wind_v * math.cos(heading_rad) + wind_u * math.sin(heading_rad)
    crosswind = wind_u * math.cos(heading_rad) - wind_v * math.sin(heading_rad)
    
    # Convert along_track to headwind convention: positive = headwind, negative = tailwind
    headwind = -along_track
    
    return {
        'tas_kmh': round(tas_kmh, 1),
        'wind_component_headwind': round(headwind, 1),
        'wind_component_crosswind': round(crosswind, 1),
        'wind_effect': 'headwind' if headwind > 0 else 'tailwind' if headwind < 0 else 'none'
    }

def meters_to_feet(meters):
    """Convert meters to feet."""
    return round(meters * 3.28084)

def kmh_to_knots(kmh):
    """Convert km/h to knots."""
    return round(kmh * 0.539957, 1)
