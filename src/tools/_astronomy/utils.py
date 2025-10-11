"""
Utility functions for astronomy tool
"""

import math


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
    
    return {
        'equatorial': {
            'right_ascension': {
                'hours': round(ra.hours, 4),
                'degrees': round(ra.degrees, 4),
                'hms': ra.hstr()
            },
            'declination': {
                'degrees': round(dec.degrees, 4),
                'dms': dec.dstr()
            }
        },
        'horizontal': {
            'altitude': {
                'degrees': round(alt.degrees, 2),
                'dms': alt.dstr()
            },
            'azimuth': {
                'degrees': round(az.degrees, 2),
                'dms': az.dstr()
            }
        },
        'distance': {
            'au': round(distance.au, 6),
            'km': round(distance.km, 0),
            'light_minutes': round(distance.au * 8.317, 2)
        },
        'is_visible': alt.degrees > 0
    }


def format_time(skyfield_time):
    """Format Skyfield time to ISO string"""
    if skyfield_time is None:
        return None
    return skyfield_time.utc_iso()


def calculate_visibility(altitude_degrees):
    """Determine visibility based on altitude
    
    Args:
        altitude_degrees: Altitude in degrees
        
    Returns:
        str: Visibility status
    """
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


def calculate_angular_separation(pos1, pos2):
    """Calculate angular separation between two positions
    
    Args:
        pos1: (ra1_deg, dec1_deg)
        pos2: (ra2_deg, dec2_deg)
        
    Returns:
        float: Angular separation in degrees
    """
    ra1, dec1 = math.radians(pos1[0]), math.radians(pos1[1])
    ra2, dec2 = math.radians(pos2[0]), math.radians(pos2[1])
    
    # Haversine formula
    dra = ra2 - ra1
    ddec = dec2 - dec1
    
    a = math.sin(ddec/2)**2 + math.cos(dec1) * math.cos(dec2) * math.sin(dra/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return math.degrees(c)


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
    
    idx = round(degrees / 22.5) % 16
    return directions[idx]
