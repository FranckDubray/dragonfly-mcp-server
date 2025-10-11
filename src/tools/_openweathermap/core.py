"""
OpenWeatherMap core business logic
"""
from .services.api_client import make_request, make_geo_request
from .utils import format_weather_data, format_forecast_data, format_air_quality


def get_current_weather(params):
    """Get current weather for city or coordinates"""
    query_params = {
        'units': params['units'],
        'lang': params['lang']
    }
    
    # Use city or coordinates
    if params.get('city'):
        query_params['q'] = params['city']
    else:
        query_params['lat'] = params['lat']
        query_params['lon'] = params['lon']
    
    data = make_request('weather', query_params)
    
    return {
        'success': True,
        'operation': 'current_weather',
        'location': {
            'name': data.get('name'),
            'country': data.get('sys', {}).get('country'),
            'coordinates': {
                'lat': data.get('coord', {}).get('lat'),
                'lon': data.get('coord', {}).get('lon')
            }
        },
        'weather': format_weather_data(data, params['units']),
        'timestamp': data.get('dt')
    }


def get_forecast_5day(params):
    """Get 5-day forecast (3-hour intervals)"""
    query_params = {
        'units': params['units'],
        'lang': params['lang']
    }
    
    if params.get('city'):
        query_params['q'] = params['city']
    else:
        query_params['lat'] = params['lat']
        query_params['lon'] = params['lon']
    
    data = make_request('forecast', query_params)
    
    return {
        'success': True,
        'operation': 'forecast_5day',
        'location': {
            'name': data.get('city', {}).get('name'),
            'country': data.get('city', {}).get('country'),
            'coordinates': {
                'lat': data.get('city', {}).get('coord', {}).get('lat'),
                'lon': data.get('city', {}).get('coord', {}).get('lon')
            }
        },
        'forecast': [format_forecast_data(item, params['units']) for item in data.get('list', [])],
        'count': len(data.get('list', []))
    }


def get_forecast_hourly(params):
    """Get hourly forecast (48 hours) via OneCall API"""
    query_params = {
        'lat': params['lat'],
        'lon': params['lon'],
        'units': params['units'],
        'lang': params['lang'],
        'exclude': 'current,minutely,daily,alerts'
    }
    
    # OneCall API is version 3.0
    data = make_request('onecall', query_params, version='3.0')
    
    hourly = data.get('hourly', [])
    
    return {
        'success': True,
        'operation': 'forecast_hourly',
        'coordinates': {
            'lat': data.get('lat'),
            'lon': data.get('lon')
        },
        'timezone': data.get('timezone'),
        'hourly_forecast': [
            {
                'timestamp': hour.get('dt'),
                'temperature': hour.get('temp'),
                'feels_like': hour.get('feels_like'),
                'pressure': hour.get('pressure'),
                'humidity': hour.get('humidity'),
                'clouds': hour.get('clouds'),
                'visibility': hour.get('visibility'),
                'wind_speed': hour.get('wind_speed'),
                'wind_deg': hour.get('wind_deg'),
                'weather': hour.get('weather', [{}])[0].get('description'),
                'pop': hour.get('pop', 0) * 100  # Probability of precipitation
            }
            for hour in hourly[:48]  # Limit to 48 hours
        ],
        'count': len(hourly[:48])
    }


def get_air_pollution(params):
    """Get air quality data"""
    query_params = {
        'lat': params['lat'],
        'lon': params['lon']
    }
    
    data = make_request('air_pollution', query_params)
    
    pollution_data = data.get('list', [{}])[0]
    components = pollution_data.get('components', {})
    aqi = pollution_data.get('main', {}).get('aqi', 0)
    
    return {
        'success': True,
        'operation': 'air_pollution',
        'coordinates': {
            'lat': data.get('coord', {}).get('lat'),
            'lon': data.get('coord', {}).get('lon')
        },
        'air_quality': format_air_quality(aqi),
        'aqi': aqi,
        'components': {
            'co': components.get('co'),  # Carbon monoxide
            'no': components.get('no'),  # Nitrogen monoxide
            'no2': components.get('no2'),  # Nitrogen dioxide
            'o3': components.get('o3'),  # Ozone
            'so2': components.get('so2'),  # Sulphur dioxide
            'pm2_5': components.get('pm2_5'),  # Fine particles
            'pm10': components.get('pm10'),  # Coarse particles
            'nh3': components.get('nh3')  # Ammonia
        },
        'timestamp': pollution_data.get('dt')
    }


def geocode_city(params):
    """Convert city name to coordinates"""
    query_params = {
        'q': params['city'],
        'limit': params['limit']
    }
    
    data = make_geo_request('direct', query_params)
    
    if not data:
        return {
            'success': False,
            'error': f"City '{params['city']}' not found"
        }
    
    return {
        'success': True,
        'operation': 'geocoding',
        'query': params['city'],
        'results': [
            {
                'name': loc.get('name'),
                'local_names': loc.get('local_names', {}),
                'lat': loc.get('lat'),
                'lon': loc.get('lon'),
                'country': loc.get('country'),
                'state': loc.get('state')
            }
            for loc in data
        ],
        'count': len(data)
    }


def reverse_geocode(params):
    """Convert coordinates to location name"""
    query_params = {
        'lat': params['lat'],
        'lon': params['lon'],
        'limit': params['limit']
    }
    
    data = make_geo_request('reverse', query_params)
    
    if not data:
        return {
            'success': False,
            'error': f"No location found for coordinates ({params['lat']}, {params['lon']})"
        }
    
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
                'local_names': loc.get('local_names', {}),
                'country': loc.get('country'),
                'state': loc.get('state')
            }
            for loc in data
        ],
        'count': len(data)
    }


def get_weather_alerts(params):
    """Get weather alerts via OneCall API"""
    query_params = {
        'lat': params['lat'],
        'lon': params['lon'],
        'units': params['units'],
        'lang': params['lang'],
        'exclude': 'current,minutely,hourly,daily'
    }
    
    # OneCall API version 3.0
    data = make_request('onecall', query_params, version='3.0')
    
    alerts = data.get('alerts', [])
    
    return {
        'success': True,
        'operation': 'weather_alerts',
        'coordinates': {
            'lat': data.get('lat'),
            'lon': data.get('lon')
        },
        'timezone': data.get('timezone'),
        'alerts': [
            {
                'sender_name': alert.get('sender_name'),
                'event': alert.get('event'),
                'start': alert.get('start'),
                'end': alert.get('end'),
                'description': alert.get('description'),
                'tags': alert.get('tags', [])
            }
            for alert in alerts
        ],
        'count': len(alerts),
        'has_alerts': len(alerts) > 0
    }


def get_onecall(params):
    """Get all-in-one weather data (current + forecast + alerts)"""
    query_params = {
        'lat': params['lat'],
        'lon': params['lon'],
        'units': params['units'],
        'lang': params['lang']
    }
    
    # Add exclusions if specified
    if params.get('exclude'):
        query_params['exclude'] = ','.join(params['exclude'])
    
    # OneCall API version 3.0
    data = make_request('onecall', query_params, version='3.0')
    
    result = {
        'success': True,
        'operation': 'onecall',
        'coordinates': {
            'lat': data.get('lat'),
            'lon': data.get('lon')
        },
        'timezone': data.get('timezone'),
        'timezone_offset': data.get('timezone_offset')
    }
    
    # Add each part if not excluded
    exclude_list = params.get('exclude', [])
    
    if 'current' not in exclude_list and 'current' in data:
        result['current'] = format_weather_data(data['current'], params['units'])
    
    if 'minutely' not in exclude_list and 'minutely' in data:
        result['minutely'] = data['minutely'][:60]  # Limit to 60 minutes
    
    if 'hourly' not in exclude_list and 'hourly' in data:
        result['hourly'] = [format_forecast_data(h, params['units']) for h in data['hourly'][:48]]
    
    if 'daily' not in exclude_list and 'daily' in data:
        result['daily'] = data['daily'][:8]  # Limit to 8 days
    
    if 'alerts' not in exclude_list and 'alerts' in data:
        result['alerts'] = data['alerts']
        result['has_alerts'] = len(data['alerts']) > 0
    
    return result
