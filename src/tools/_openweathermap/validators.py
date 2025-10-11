"""
Input validation for OpenWeatherMap operations
"""


def validate_params(params):
    """Validate and normalize parameters"""
    operation = params.get('operation')
    if not operation:
        raise ValueError("Missing required parameter: operation")
    
    # Validate operation-specific requirements
    if operation in ['current_weather', 'forecast_5day']:
        if not params.get('city') and not (params.get('lat') and params.get('lon')):
            raise ValueError(f"{operation} requires either 'city' or 'lat'+'lon'")
    
    elif operation in ['air_pollution', 'reverse_geocoding', 'weather_alerts', 'onecall', 'forecast_hourly']:
        if not (params.get('lat') and params.get('lon')):
            raise ValueError(f"{operation} requires 'lat' and 'lon'")
    
    elif operation == 'geocoding':
        if not params.get('city'):
            raise ValueError("geocoding requires 'city'")
    
    # Validate coordinates if provided
    if 'lat' in params:
        lat = params['lat']
        if not isinstance(lat, (int, float)) or lat < -90 or lat > 90:
            raise ValueError("lat must be a number between -90 and 90")
    
    if 'lon' in params:
        lon = params['lon']
        if not isinstance(lon, (int, float)) or lon < -180 or lon > 180:
            raise ValueError("lon must be a number between -180 and 180")
    
    # Set defaults
    validated = params.copy()
    validated.setdefault('units', 'metric')
    validated.setdefault('lang', 'en')
    validated.setdefault('limit', 5)
    
    return validated
