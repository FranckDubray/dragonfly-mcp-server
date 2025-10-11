"""
OpenWeatherMap API routing
"""
from .validators import validate_params
from .core import (
    get_current_weather,
    get_forecast_5day,
    get_forecast_hourly,
    get_air_pollution,
    geocode_city,
    reverse_geocode,
    get_weather_alerts,
    get_onecall
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
        elif operation == 'forecast_5day':
            return get_forecast_5day(validated)
        elif operation == 'forecast_hourly':
            return get_forecast_hourly(validated)
        elif operation == 'air_pollution':
            return get_air_pollution(validated)
        elif operation == 'geocoding':
            return geocode_city(validated)
        elif operation == 'reverse_geocoding':
            return reverse_geocode(validated)
        elif operation == 'weather_alerts':
            return get_weather_alerts(validated)
        elif operation == 'onecall':
            return get_onecall(validated)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }
