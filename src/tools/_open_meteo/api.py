"""
Open-Meteo API routing
"""
from .validators import validate_params
from .core import (
    get_current_weather,
    get_forecast_hourly,
    get_forecast_daily,
    get_air_quality,
    geocode_location,
    reverse_geocode
)


def route_operation(**params):
    """Route to appropriate handler based on operation"""
    try:
        # Validate and normalize params
        validated = validate_params(params)
        operation = validated['operation']
        
        # Route to handlers
        if operation == 'current_weather':
            return get_current_weather(validated)
        elif operation == 'forecast_hourly':
            return get_forecast_hourly(validated)
        elif operation == 'forecast_daily':
            return get_forecast_daily(validated)
        elif operation == 'air_quality':
            return get_air_quality(validated)
        elif operation == 'geocoding':
            return geocode_location(validated)
        elif operation == 'reverse_geocoding':
            return reverse_geocode(validated)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }
