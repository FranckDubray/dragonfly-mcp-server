"""
API routing for astronomy operations with basic logging
"""

import logging
from . import validators
from . import core

logger = logging.getLogger(__name__)


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
        logger.info("astronomy: operation=%s", operation)
        
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
            logger.warning("astronomy: iss_position requested but offline placeholder will be returned")
            return handle_iss_position(params)
        elif operation == 'star_position':
            return handle_star_position(params)
        else:
            logger.error("astronomy: unknown operation=%s", operation)
            return {
                'success': False,
                'error': f'Unknown operation: {operation}'
            }
    
    except ValueError as e:
        logger.warning("astronomy: validation error: %s", e)
        return {
            'success': False,
            'error': f'Validation error: {str(e)}'
        }
    except Exception as e:
        logger.exception("astronomy: unexpected error")
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def handle_planet_position(params):
    """Handle planet_position operation"""
    body = validators.validate_body(params, required=True)
    lat, lon = validators.validate_coordinates(params, required=True)
    elevation = validators.validate_elevation(params)
    date = validators.validate_date(params)
    
    return core.planet_position({
        'body': body,
        'latitude': lat,
        'longitude': lon,
        'elevation': elevation,
        'date': date
    })


def handle_moon_phase(params):
    """Handle moon_phase operation"""
    date = validators.validate_date(params)
    return core.moon_phase_operation({'date': date})


def handle_sun_moon_times(params):
    """Handle sun_moon_times operation"""
    lat, lon = validators.validate_coordinates(params, required=True)
    elevation = validators.validate_elevation(params)
    date = validators.validate_date(params)
    
    return core.sun_moon_times_operation({
        'latitude': lat,
        'longitude': lon,
        'elevation': elevation,
        'date': date
    })


def handle_celestial_events(params):
    """Handle celestial_events operation"""
    date = validators.validate_date(params)
    days = validators.validate_days(params)
    limit = params.get('limit')
    
    payload = {'date': date, 'days': days}
    if limit is not None:
        payload['limit'] = limit
    
    return core.celestial_events_operation(payload)


def handle_planet_info(params):
    """Handle planet_info operation"""
    body = validators.validate_body(params, required=True)
    return core.planet_info_operation({'body': body})


def handle_visible_planets(params):
    """Handle visible_planets operation"""
    lat, lon = validators.validate_coordinates(params, required=True)
    elevation = validators.validate_elevation(params)
    date = validators.validate_date(params)
    
    return core.visible_planets_operation({
        'latitude': lat,
        'longitude': lon,
        'elevation': elevation,
        'date': date
    })


def handle_iss_position(params):
    """Handle iss_position operation (offline placeholder)"""
    # Coordinates and date are optional and currently unused in placeholder
    _ = validators.validate_coordinates(params, required=False)
    elevation = validators.validate_elevation(params)
    date = validators.validate_date(params)
    
    return core.iss_position_operation({
        'elevation': elevation,
        'date': date
    })


def handle_star_position(params):
    """Handle star_position operation"""
    star_name = validators.validate_star_name(params, required=True)
    lat, lon = validators.validate_coordinates(params, required=True)
    elevation = validators.validate_elevation(params)
    date = validators.validate_date(params)
    
    return core.star_position_operation({
        'star_name': star_name,
        'latitude': lat,
        'longitude': lon,
        'elevation': elevation,
        'date': date
    })
