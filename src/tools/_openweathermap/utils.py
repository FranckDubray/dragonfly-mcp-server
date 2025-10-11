"""
Utility functions for OpenWeatherMap
"""


def format_weather_data(data, units):
    """Format weather data consistently"""
    temp_unit = '°C' if units == 'metric' else ('°F' if units == 'imperial' else 'K')
    speed_unit = 'm/s' if units == 'metric' else 'mph'
    
    weather_list = data.get('weather', [])
    weather_main = weather_list[0] if weather_list else {}
    
    return {
        'temperature': data.get('temp'),
        'temperature_unit': temp_unit,
        'feels_like': data.get('feels_like'),
        'pressure': data.get('pressure'),  # hPa
        'humidity': data.get('humidity'),  # %
        'clouds': data.get('clouds'),  # %
        'visibility': data.get('visibility'),  # meters
        'wind_speed': data.get('wind_speed'),
        'wind_speed_unit': speed_unit,
        'wind_deg': data.get('wind_deg'),
        'description': weather_main.get('description'),
        'main': weather_main.get('main'),
        'icon': weather_main.get('icon')
    }


def format_forecast_data(data, units):
    """Format forecast item data"""
    temp_unit = '°C' if units == 'metric' else ('°F' if units == 'imperial' else 'K')
    
    weather_list = data.get('weather', [])
    weather_main = weather_list[0] if weather_list else {}
    
    # Handle both main.temp (onecall) and temp (forecast)
    main = data.get('main', {})
    
    return {
        'timestamp': data.get('dt'),
        'datetime_text': data.get('dt_txt'),  # Only in 5-day forecast
        'temperature': data.get('temp') or main.get('temp'),
        'temperature_unit': temp_unit,
        'feels_like': data.get('feels_like') or main.get('feels_like'),
        'temp_min': main.get('temp_min'),
        'temp_max': main.get('temp_max'),
        'pressure': data.get('pressure') or main.get('pressure'),
        'humidity': data.get('humidity') or main.get('humidity'),
        'clouds': data.get('clouds', {}).get('all') if isinstance(data.get('clouds'), dict) else data.get('clouds'),
        'wind_speed': data.get('wind_speed') or data.get('wind', {}).get('speed'),
        'wind_deg': data.get('wind_deg') or data.get('wind', {}).get('deg'),
        'weather': weather_main.get('description'),
        'pop': data.get('pop', 0) * 100 if data.get('pop') else None  # Probability of precipitation
    }


def format_air_quality(aqi):
    """
    Format AQI to human-readable quality level
    
    AQI scale:
    1 = Good
    2 = Fair
    3 = Moderate
    4 = Poor
    5 = Very Poor
    """
    quality_map = {
        1: 'Good',
        2: 'Fair',
        3: 'Moderate',
        4: 'Poor',
        5: 'Very Poor'
    }
    return quality_map.get(aqi, 'Unknown')
