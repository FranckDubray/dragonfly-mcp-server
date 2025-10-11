"""
Parameter validation for astronomy operations
"""

from datetime import datetime, timezone


def validate_operation(params):
    """Validate operation parameter"""
    operation = params.get('operation')
    if not operation:
        raise ValueError("Missing required parameter: operation")
    
    valid_operations = [
        'planet_position', 'moon_phase', 'sun_moon_times', 
        'celestial_events', 'planet_info', 'visible_planets',
        'iss_position', 'star_position'
    ]
    
    if operation not in valid_operations:
        raise ValueError(f"Invalid operation: {operation}")
    
    return operation


def validate_body(params, required=True):
    """Validate body parameter"""
    body = params.get('body')
    
    if required and not body:
        raise ValueError("Missing required parameter: body")
    
    if body:
        valid_bodies = [
            'sun', 'moon', 'mercury', 'venus', 'mars',
            'jupiter', 'saturn', 'uranus', 'neptune', 'pluto'
        ]
        
        if body.lower() not in valid_bodies:
            raise ValueError(f"Invalid body: {body}")
    
    return body.lower() if body else None


def validate_coordinates(params, required=False):
    """Validate latitude and longitude"""
    lat = params.get('latitude')
    lon = params.get('longitude')
    
    if required and (lat is None or lon is None):
        raise ValueError("Missing required parameters: latitude and longitude")
    
    if lat is not None:
        if not isinstance(lat, (int, float)):
            raise ValueError("latitude must be a number")
        if lat < -90 or lat > 90:
            raise ValueError("latitude must be between -90 and 90")
    
    if lon is not None:
        if not isinstance(lon, (int, float)):
            raise ValueError("longitude must be a number")
        if lon < -180 or lon > 180:
            raise ValueError("longitude must be between -180 and 180")
    
    return lat, lon


def validate_elevation(params):
    """Validate elevation parameter"""
    elevation = params.get('elevation', 0)
    
    if not isinstance(elevation, (int, float)):
        raise ValueError("elevation must be a number")
    
    if elevation < -500 or elevation > 9000:
        raise ValueError("elevation must be between -500 and 9000 meters")
    
    return elevation


def validate_date(params):
    """Validate and parse date parameter
    
    Returns:
        datetime object (UTC)
    """
    date_str = params.get('date')
    
    if not date_str:
        # Default to now (UTC)
        return datetime.now(timezone.utc)
    
    # Try parsing ISO format
    try:
        # Try with time
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            # Date only, set time to 00:00
            dt = datetime.fromisoformat(date_str)
            dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Ensure UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        
        return dt
        
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Use ISO 8601 (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")


def validate_days(params):
    """Validate days parameter"""
    days = params.get('days', 7)
    
    if not isinstance(days, int):
        raise ValueError("days must be an integer")
    
    if days < 1 or days > 30:
        raise ValueError("days must be between 1 and 30")
    
    return days


def validate_star_name(params, required=True):
    """Validate star_name parameter"""
    star_name = params.get('star_name')
    
    if required and not star_name:
        raise ValueError("Missing required parameter: star_name")
    
    return star_name


def validate_horizon(params):
    """Validate horizon parameter"""
    horizon = params.get('horizon', -6)
    
    if not isinstance(horizon, (int, float)):
        raise ValueError("horizon must be a number")
    
    if horizon < -18 or horizon > 0:
        raise ValueError("horizon must be between -18 and 0 degrees")
    
    return horizon
