"""
Split from core.py: weather operations
"""
from .services.api_client import make_forecast_request, make_air_quality_request
from .utils_weather import (
    format_current_weather,
    format_hourly_forecast,
    format_daily_forecast,
)


def get_current_weather(params):
    query_params = {
        'latitude': params['lat'],
        'longitude': params['lon'],
        'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m',
        'temperature_unit': params['temperature_unit'],
        'wind_speed_unit': params['wind_speed_unit'],
        'precipitation_unit': params['precipitation_unit'],
        'timezone': params['timezone']
    }
    data = make_forecast_request(query_params)
    return {
        'coordinates': {'lat': data.get('latitude'), 'lon': data.get('longitude')},
        'timezone': data.get('timezone'),
        'elevation': data.get('elevation'),
        'current': format_current_weather(data.get('current', {}), data.get('current_units', {}))
    }


def get_forecast_hourly(params):
    query_params = {
        'latitude': params['lat'],
        'longitude': params['lon'],
        'hourly': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,weather_code,cloud_cover,pressure_msl,surface_pressure,visibility,wind_speed_10m,wind_direction_10m,wind_gusts_10m,uv_index',
        'temperature_unit': params['temperature_unit'],
        'wind_speed_unit': params['wind_speed_unit'],
        'precipitation_unit': params['precipitation_unit'],
        'timezone': params['timezone'],
        'forecast_days': min(7, (params['forecast_hours'] // 24) + 1),
        'past_days': params['past_days']
    }
    data = make_forecast_request(query_params)
    hourly = data.get('hourly', {})
    times = hourly.get('time', [])
    limit = params['forecast_hours']
    formatted = format_hourly_forecast(hourly, data.get('hourly_units', {}), limit)

    # Backward-compatible handling: formatted may be a list (old) or dict (new)
    if isinstance(formatted, dict):
        items = formatted.get('items', [])
        returned = formatted.get('returned_count', len(items))
        total = formatted.get('total_count', len(times))
        truncated = formatted.get('truncated', total > returned)
    else:
        items = formatted
        returned = len(items)
        total = len(times)
        truncated = total > returned

    result = {
        'coordinates': {'lat': data.get('latitude'), 'lon': data.get('longitude')},
        'timezone': data.get('timezone'),
        'elevation': data.get('elevation'),
        'hourly_forecast': items,
        'returned_count': returned,
        'total_count': total,
        'truncated': truncated,
    }
    if truncated:
        result['message'] = 'Hourly forecast truncated to forecast_hours limit'
    return result


def get_forecast_daily(params):
    query_params = {
        'latitude': params['lat'],
        'longitude': params['lon'],
        'daily': 'weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,daylight_duration,sunshine_duration,uv_index_max,precipitation_sum,precipitation_hours,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant',
        'temperature_unit': params['temperature_unit'],
        'wind_speed_unit': params['wind_speed_unit'],
        'precipitation_unit': params['precipitation_unit'],
        'timezone': params['timezone'],
        'forecast_days': params['forecast_days'],
        'past_days': params['past_days']
    }
    data = make_forecast_request(query_params)
    daily = data.get('daily', {})
    items = format_daily_forecast(daily, data.get('daily_units', {}))
    return {
        'coordinates': {'lat': data.get('latitude'), 'lon': data.get('longitude')},
        'timezone': data.get('timezone'),
        'elevation': data.get('elevation'),
        'daily_forecast': items,
        'returned_count': len(items),
        'total_count': len(daily.get('time', []) or []),
        'truncated': False,
    }


def get_air_quality(params):
    query_params = {
        'latitude': params['lat'],
        'longitude': params['lon'],
        'current': 'european_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,dust,uv_index,aerosol_optical_depth',
        'timezone': params['timezone']
    }
    data = make_air_quality_request(query_params)
    return {
        'coordinates': {'lat': data.get('latitude'), 'lon': data.get('longitude')},
        'timezone': data.get('timezone'),
        'elevation': data.get('elevation'),
        'air_quality': {
            'time': data.get('current', {}).get('time'),
            'european_aqi': data.get('current', {}).get('european_aqi'),
            'pm10': data.get('current', {}).get('pm10'),
            'pm2_5': data.get('current', {}).get('pm2_5'),
            'ozone': data.get('current', {}).get('ozone'),
        }
    }
