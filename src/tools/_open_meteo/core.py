"""
Open-Meteo core business logic
"""
from .services.api_client import make_forecast_request, make_air_quality_request, make_geocoding_request
from .utils import format_current_weather, format_hourly_forecast, format_daily_forecast, format_air_quality


def get_current_weather(params):
    """Get current weather for coordinates"""
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
        'success': True,
        'operation': 'current_weather',
        'coordinates': {
            'lat': data.get('latitude'),
            'lon': data.get('longitude')
        },
        'timezone': data.get('timezone'),
        'elevation': data.get('elevation'),
        'current': format_current_weather(data.get('current', {}), data.get('current_units', {}))
    }


def get_forecast_hourly(params):
    """Get hourly weather forecast"""
    query_params = {
        'latitude': params['lat'],
        'longitude': params['lon'],
        'hourly': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,weather_code,cloud_cover,pressure_msl,surface_pressure,visibility,wind_speed_10m,wind_direction_10m,wind_gusts_10m,uv_index',
        'temperature_unit': params['temperature_unit'],
        'wind_speed_unit': params['wind_speed_unit'],
        'precipitation_unit': params['precipitation_unit'],
        'timezone': params['timezone'],
        'forecast_days': min(7, (params['forecast_hours'] // 24) + 1),  # Calculate days needed
        'past_days': params['past_days']
    }
    
    data = make_forecast_request(query_params)
    
    hourly = data.get('hourly', {})
    times = hourly.get('time', [])
    
    # Limit to requested hours
    limit = params['forecast_hours']
    
    return {
        'success': True,
        'operation': 'forecast_hourly',
        'coordinates': {
            'lat': data.get('latitude'),
            'lon': data.get('longitude')
        },
        'timezone': data.get('timezone'),
        'elevation': data.get('elevation'),
        'hourly_forecast': format_hourly_forecast(hourly, data.get('hourly_units', {}), limit),
        'forecast_hours': min(len(times), limit)
    }


def get_forecast_daily(params):
    """Get daily weather forecast"""
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
    
    return {
        'success': True,
        'operation': 'forecast_daily',
        'coordinates': {
            'lat': data.get('latitude'),
            'lon': data.get('longitude')
        },
        'timezone': data.get('timezone'),
        'elevation': data.get('elevation'),
        'daily_forecast': format_daily_forecast(data.get('daily', {}), data.get('daily_units', {})),
        'forecast_days': params['forecast_days']
    }


def get_air_quality(params):
    """Get air quality data"""
    query_params = {
        'latitude': params['lat'],
        'longitude': params['lon'],
        'current': 'european_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,dust,uv_index,aerosol_optical_depth',
        'timezone': params['timezone']
    }
    
    data = make_air_quality_request(query_params)
    
    return {
        'success': True,
        'operation': 'air_quality',
        'coordinates': {
            'lat': data.get('latitude'),
            'lon': data.get('longitude')
        },
        'timezone': data.get('timezone'),
        'elevation': data.get('elevation'),
        'air_quality': format_air_quality(data.get('current', {}), data.get('current_units', {}))
    }


def geocode_location(params):
    """Convert location name to coordinates"""
    query_params = {
        'name': params['location'],
        'count': params['limit'],
        'language': params['language'],
        'format': 'json'
    }
    
    data = make_geocoding_request(query_params)
    
    results = data.get('results', [])
    
    if not results:
        return {
            'success': False,
            'error': f"Location '{params['location']}' not found"
        }
    
    return {
        'success': True,
        'operation': 'geocoding',
        'query': params['location'],
        'results': [
            {
                'name': loc.get('name'),
                'lat': loc.get('latitude'),
                'lon': loc.get('longitude'),
                'country': loc.get('country'),
                'country_code': loc.get('country_code'),
                'admin1': loc.get('admin1'),  # State/region
                'admin2': loc.get('admin2'),  # County
                'timezone': loc.get('timezone'),
                'elevation': loc.get('elevation'),
                'population': loc.get('population')
            }
            for loc in results
        ],
        'count': len(results)
    }


def reverse_geocode(params):
    """Get location name from coordinates"""
    # Open-Meteo doesn't have dedicated reverse geocoding
    # We'll search nearby locations using coordinates as reference
    query_params = {
        'name': f"{params['lat']},{params['lon']}",
        'count': params['limit'],
        'language': params['language'],
        'format': 'json'
    }
    
    data = make_geocoding_request(query_params)
    
    results = data.get('results', [])
    
    if not results:
        return {
            'success': False,
            'error': f"No location found near coordinates ({params['lat']}, {params['lon']})"
        }
    
    # Sort by distance to input coordinates
    def distance(loc):
        """Simple distance calculation"""
        lat_diff = abs(loc.get('latitude', 0) - params['lat'])
        lon_diff = abs(loc.get('longitude', 0) - params['lon'])
        return lat_diff + lon_diff
    
    sorted_results = sorted(results, key=distance)
    
    return {
        'success': True,
        'operation': 'reverse_geocoding',
        'coordinates': {
            'lat': params['lat'],
            'lon': params['lon']
        },
        'results': [
            {
                'name': loc.get('name'),
                'lat': loc.get('latitude'),
                'lon': loc.get('longitude'),
                'country': loc.get('country'),
                'country_code': loc.get('country_code'),
                'admin1': loc.get('admin1'),
                'admin2': loc.get('admin2'),
                'timezone': loc.get('timezone'),
                'elevation': loc.get('elevation')
            }
            for loc in sorted_results
        ],
        'count': len(sorted_results)
    }
