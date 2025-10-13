"""
Utilities for weather formatting and descriptions (Open-Meteo)
"""

def format_current_weather(current, units):
    return {
        'time': current.get('time'),
        'temperature': current.get('temperature_2m'),
        'temperature_unit': units.get('temperature_2m'),
        'apparent_temperature': current.get('apparent_temperature'),
        'humidity': current.get('relative_humidity_2m'),
        'humidity_unit': units.get('relative_humidity_2m'),
        'precipitation': current.get('precipitation'),
        'precipitation_unit': units.get('precipitation'),
        'weather_code': current.get('weather_code'),
        'weather_description': get_weather_description(current.get('weather_code')),
        'cloud_cover': current.get('cloud_cover'),
        'cloud_cover_unit': units.get('cloud_cover'),
        'pressure_msl': current.get('pressure_msl'),
        'pressure_msl_unit': units.get('pressure_msl'),
        'surface_pressure': current.get('surface_pressure'),
        'surface_pressure_unit': units.get('surface_pressure'),
        'wind_speed': current.get('wind_speed_10m'),
        'wind_speed_unit': units.get('wind_speed_10m'),
        'wind_direction': current.get('wind_direction_10m'),
        'wind_direction_unit': units.get('wind_direction_10m'),
        'wind_gusts': current.get('wind_gusts_10m'),
        'wind_gusts_unit': units.get('wind_gusts_10m')
    }


def format_hourly_forecast(hourly, units, limit):
    times = hourly.get('time', [])
    count = min(len(times), limit)
    forecast = []
    for i in range(count):
        forecast.append({
            'time': times[i],
            'temperature': get_value_at_index(hourly, 'temperature_2m', i),
            'apparent_temperature': get_value_at_index(hourly, 'apparent_temperature', i),
            'humidity': get_value_at_index(hourly, 'relative_humidity_2m', i),
            'precipitation_probability': get_value_at_index(hourly, 'precipitation_probability', i),
            'precipitation': get_value_at_index(hourly, 'precipitation', i),
            'weather_code': get_value_at_index(hourly, 'weather_code', i),
            'weather_description': get_weather_description(get_value_at_index(hourly, 'weather_code', i)),
            'cloud_cover': get_value_at_index(hourly, 'cloud_cover', i),
            'pressure_msl': get_value_at_index(hourly, 'pressure_msl', i),
            'surface_pressure': get_value_at_index(hourly, 'surface_pressure', i),
            'visibility': get_value_at_index(hourly, 'visibility', i),
            'wind_speed': get_value_at_index(hourly, 'wind_speed_10m', i),
            'wind_direction': get_value_at_index(hourly, 'wind_direction_10m', i),
            'wind_gusts': get_value_at_index(hourly, 'wind_gusts_10m', i),
            'uv_index': get_value_at_index(hourly, 'uv_index', i)
        })
    return forecast


def format_daily_forecast(daily, units):
    times = daily.get('time', [])
    forecast = []
    for i in range(len(times)):
        forecast.append({
            'date': times[i],
            'weather_code': get_value_at_index(daily, 'weather_code', i),
            'weather_description': get_weather_description(get_value_at_index(daily, 'weather_code', i)),
            'temperature_max': get_value_at_index(daily, 'temperature_2m_max', i),
            'temperature_min': get_value_at_index(daily, 'temperature_2m_min', i),
            'apparent_temperature_max': get_value_at_index(daily, 'apparent_temperature_max', i),
            'apparent_temperature_min': get_value_at_index(daily, 'apparent_temperature_min', i),
            'sunrise': get_value_at_index(daily, 'sunrise', i),
            'sunset': get_value_at_index(daily, 'sunset', i),
            'daylight_duration': get_value_at_index(daily, 'daylight_duration', i),
            'sunshine_duration': get_value_at_index(daily, 'sunshine_duration', i),
            'uv_index_max': get_value_at_index(daily, 'uv_index_max', i),
            'precipitation_sum': get_value_at_index(daily, 'precipitation_sum', i),
            'precipitation_hours': get_value_at_index(daily, 'precipitation_hours', i),
            'precipitation_probability_max': get_value_at_index(daily, 'precipitation_probability_max', i),
            'wind_speed_max': get_value_at_index(daily, 'wind_speed_10m_max', i),
            'wind_gusts_max': get_value_at_index(daily, 'wind_gusts_10m_max', i),
            'wind_direction_dominant': get_value_at_index(daily, 'wind_direction_10m_dominant', i)
        })
    return forecast


def get_value_at_index(data, key, index):
    values = data.get(key, [])
    if index < len(values):
        return values[index]
    return None


def get_weather_description(code):
    if code is None:
        return "Unknown"
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return weather_codes.get(code, f"Unknown ({code})")
