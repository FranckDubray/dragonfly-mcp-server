"""
Utility functions for astronomy tool
"""

import math
import json


def format_position(astrometric, observer_time):
    """Format celestial position data
    
    Args:
        astrometric: Skyfield Astrometric object
        observer_time: Time of observation
        
    Returns:
        dict with formatted position data
    """
    # Apparent position
    apparent = astrometric.apparent()
    
    # RA/Dec (equatorial coordinates)
    ra, dec, distance = apparent.radec()
    
    # Alt/Az (horizontal coordinates)
    alt, az, _ = apparent.altaz()
    
    # Build result dict with explicit type conversions
    result = {
        'equatorial': {
            'right_ascension': {
                'hours': float(ra.hours),
                'degrees': float(ra.degrees),
                'hms': str(ra.hstr())
            },
            'declination': {
                'degrees': float(dec.degrees),
                'dms': str(dec.dstr())
            }
        },
        'horizontal': {
            'altitude': {
                'degrees': float(alt.degrees),
                'dms': str(alt.dstr())
            },
            'azimuth': {
                'degrees': float(az.degrees),
                'dms': str(az.dstr())
            }
        },
        'distance': {
            'au': float(distance.au),
            'km': float(distance.km),
            'light_minutes': float(distance.au * 8.317)
        },
        'is_visible': bool(float(alt.degrees) > 0)
    }
    
    # Force JSON serialization test to catch any remaining issues
    try:
        json.dumps(result)
    except TypeError:
        # If serialization fails, recursively convert all values
        result = _deep_convert(result)
    
    return result


def _deep_convert(obj):
    """Recursively convert all non-serializable types"""
    if isinstance(obj, dict):
        return {k: _deep_convert(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_deep_convert(v) for v in obj]
    elif hasattr(obj, 'item'):  # numpy
        return obj.item()
    elif hasattr(obj, '__float__'):
        return float(obj)
    elif hasattr(obj, '__int__'):
        return int(obj)
    elif hasattr(obj, '__bool__'):
        return bool(obj)
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)


def calculate_visibility(altitude_degrees):
    """Determine visibility based on altitude
    
    Args:
        altitude_degrees: Altitude in degrees
        
    Returns:
        str: Visibility status
    """
    altitude_degrees = float(altitude_degrees)  # Ensure Python float
    
    if altitude_degrees < -18:
        return "Below horizon (not visible)"
    elif altitude_degrees < -12:
        return "Astronomical twilight"
    elif altitude_degrees < -6:
        return "Nautical twilight"
    elif altitude_degrees < 0:
        return "Civil twilight"
    elif altitude_degrees < 10:
        return "Low on horizon (may be difficult to see)"
    elif altitude_degrees < 30:
        return "Visible (low)"
    elif altitude_degrees < 60:
        return "Visible (medium height)"
    else:
        return "Visible (high in sky)"


def format_physical_data(data):
    """Format physical characteristics data
    
    Args:
        Raw planet data dict
        
    Returns:
        Formatted dict with units
    """
    formatted = {}
    
    for key, value in data.items():
        if key == 'mass_kg':
            formatted['mass'] = {
                'value': value,
                'unit': 'kg',
                'scientific_notation': f"{value:.4e}"
            }
        elif key == 'diameter_km':
            formatted['diameter'] = {
                'value': value,
                'unit': 'km'
            }
        elif key == 'surface_temperature_k':
            if isinstance(value, dict):
                formatted['surface_temperature'] = {
                    'min_kelvin': value.get('min'),
                    'max_kelvin': value.get('max'),
                    'mean_kelvin': value.get('mean'),
                    'min_celsius': value.get('min') - 273.15 if value.get('min') else None,
                    'max_celsius': value.get('max') - 273.15 if value.get('max') else None,
                    'mean_celsius': value.get('mean') - 273.15 if value.get('mean') else None
                }
            else:
                formatted['surface_temperature'] = {
                    'kelvin': value,
                    'celsius': value - 273.15
                }
        elif key == 'distance_from_sun_au':
            formatted['distance_from_sun'] = {
                'au': value,
                'million_km': data.get('distance_from_sun_million_km')
            }
        elif key not in ['distance_from_sun_million_km']:
            formatted[key] = value
    
    return formatted


def degrees_to_cardinal(degrees):
    """Convert azimuth degrees to cardinal direction
    
    Args:
        degrees: Azimuth in degrees (0-360)
        
    Returns:
        str: Cardinal direction (N, NE, E, etc.)
    """
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    
    idx = round(float(degrees) / 22.5) % 16
    return directions[idx]
