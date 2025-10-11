"""
API routing for astronomy operations
"""

from . import validators
from . import core


def route_operation(params):
    """Route to appropriate operation handler
    
    Args:
        params: Request parameters
        
    Returns:
        Operation result dict
    """
    try:
        # Validate operation
        operation = validators.validate_operation(params)
        
        # Route to handler
        if operation == 'planet_position':
            return handle_planet_position(params)
        elif operation == 'moon_phase':
            return handle_moon_phase(params)
        elif operation == 'sun_moon_times':
            return handle_sun_moon_times(params)
        elif operation == 'celestial_events':
            return handle_celestial_events(params)
        elif operation == 'planet_info':
            return handle_planet_info(params)
        elif operation == 'visible_planets':
            return handle_visible_planets(params)
        elif operation == 'iss_position':
            return handle_iss_position(params)
        elif operation == 'star_position':
            return handle_star_position(params)
        else:
            return {
                'success': False,
                'error': f'Unknown operation: {operation}'
            }
    
    except ValueError as e:
        return {
            'success': False,
            'error': f'Validation error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def handle_planet_position(params):
    """Handle planet_position operation"""
    # Validate parameters
    body = validators.validate_body(params, required=True)
    lat, lon = validators.validate_coordinates(params, required=True)
    elevation = validators.validate_elevation(params)
    date = validators.validate_date(params)
    
    # Execute operation
    return core.planet_position({
        'body': body,
        'latitude': lat,
        'longitude': lon,
        'elevation': elevation,
        'date': date
    })


def handle_moon_phase(params):
    """Handle moon_phase operation"""
    # Validate parameters
    date = validators.validate_date(params)
    
    # Execute operation
    return core.moon_phase_operation({
        'date': date
    })


def handle_sun_moon_times(params):
    """Handle sun_moon_times operation"""
    # Validate parameters
    lat, lon = validators.validate_coordinates(params, required=True)
    elevation = validators.validate_elevation(params)
    date = validators.validate_date(params)
    
    # Execute operation
    return core.sun_moon_times_operation({
        'latitude': lat,
        'longitude': lon,
        'elevation': elevation,
        'date': date
    })


def handle_celestial_events(params):
    """Handle celestial_events operation"""
    # Validate parameters
    date = validators.validate_date(params)
    days = validators.validate_days(params)
    
    # Execute operation
    return core.celestial_events_operation({
        'date': date,
        'days': days
    })


def handle_planet_info(params):
    """Handle planet_info operation"""
    # Validate parameters
    body = validators.validate_body(params, required=True)
    
    # Execute operation
    return core.planet_info_operation({
        'body': body
    })


def handle_visible_planets(params):
    """Handle visible_planets operation"""
    # Validate parameters
    lat, lon = validators.validate_coordinates(params, required=True)
    elevation = validators.validate_elevation(params)
    date = validators.validate_date(params)
    
    # Execute operation
    return core.visible_planets_operation({
        'latitude': lat,
        'longitude': lon,
        'elevation': elevation,
        'date': date
    })


def handle_iss_position(params):
    """Handle iss_position operation"""
    # Validate parameters
    lat, lon = validators.validate_coordinates(params, required=False)
    elevation = validators.validate_elevation(params)
    date = validators.validate_date(params)
    
    # Execute operation
    return core.iss_position_operation({
        'latitude': lat,
        'longitude': lon,
        'elevation': elevation,
        'date': date
    })


def handle_star_position(params):
    """Handle star_position operation"""
    # Validate parameters
    star_name = validators.validate_star_name(params, required=True)
    lat, lon = validators.validate_coordinates(params, required=True)
    elevation = validators.validate_elevation(params)
    date = validators.validate_date(params)
    
    # Execute operation
    return core.star_position_operation({
        'star_name': star_name,
        'latitude': lat,
        'longitude': lon,
        'elevation': elevation,
        'date': date
    })
