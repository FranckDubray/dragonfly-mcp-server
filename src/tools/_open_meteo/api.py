"""
Open-Meteo API routing (minimal outputs, strict errors)
"""
import logging
from .validators import validate_params
from .core_weather import (
    get_current_weather,
    get_forecast_hourly,
    get_forecast_daily,
    get_air_quality,
)
from .core_geo import (
    geocode_location,
    reverse_geocode,
)

LOG = logging.getLogger(__name__)


def route_operation(**params):
    """Route to appropriate handler based on validated operation.

    Raises exceptions on error (no verbose metadata in outputs).
    """
    try:
        validated = validate_params(params)
        operation = validated['operation']

        if operation == 'current_weather':
            return get_current_weather(validated)
        if operation == 'forecast_hourly':
            return get_forecast_hourly(validated)
        if operation == 'forecast_daily':
            return get_forecast_daily(validated)
        if operation == 'air_quality':
            return get_air_quality(validated)
        if operation == 'geocoding':
            return geocode_location(validated)
        if operation == 'reverse_geocoding':
            return reverse_geocode(validated)

        raise ValueError(f"Unknown operation: {operation}")
    except Exception as e:
        LOG.error(f"open_meteo operation failed: {e}")
        # Re-raise to let upstream format the error minimally
        raise
