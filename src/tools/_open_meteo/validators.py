"""
Input validation for Open-Meteo operations
"""


def validate_params(params):
    """Validate and normalize parameters"""
    operation = params.get('operation')
    if not operation:
        raise ValueError("Missing required parameter: operation")
    
    # Validate operation-specific requirements
    if operation in ['current_weather', 'forecast_hourly', 'forecast_daily', 'air_quality']:
        if not (params.get('lat') is not None and params.get('lon') is not None):
            raise ValueError(f"{operation} requires 'lat' and 'lon' coordinates")
    
    elif operation == 'geocoding':
        if not params.get('location'):
            raise ValueError("geocoding requires 'location' name")
    
    elif operation == 'reverse_geocoding':
        if not (params.get('lat') is not None and params.get('lon') is not None):
            raise ValueError("reverse_geocoding requires 'lat' and 'lon' coordinates")
    
    # Validate coordinates if provided
    if 'lat' in params and params['lat'] is not None:
        lat = params['lat']
        if not isinstance(lat, (int, float)) or lat < -90 or lat > 90:
            raise ValueError("lat must be a number between -90 and 90")
    
    if 'lon' in params and params['lon'] is not None:
        lon = params['lon']
        if not isinstance(lon, (int, float)) or lon < -180 or lon > 180:
            raise ValueError("lon must be a number between -180 and 180")
    
    # Set defaults
    validated = params.copy()
    validated.setdefault('temperature_unit', 'celsius')
    validated.setdefault('wind_speed_unit', 'kmh')
    validated.setdefault('precipitation_unit', 'mm')
    validated.setdefault('timezone', 'auto')
    validated.setdefault('forecast_days', 7)
    validated.setdefault('forecast_hours', 24)
    validated.setdefault('past_days', 0)
    validated.setdefault('language', 'en')
    validated.setdefault('limit', 5)
    
    return validated
