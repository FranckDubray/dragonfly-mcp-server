"""
Split from core.py: geocoding operations
"""
from .services.api_client import make_geocoding_request


def geocode_location(params):
    query_params = {
        'name': params['location'],
        'count': params['limit'],
        'language': params['language'],
        'format': 'json'
    }
    data = make_geocoding_request(query_params)
    results = data.get('results', [])
    if not results:
        return {'error': f"Location '{params['location']}' not found"}
    return {
        'query': params['location'],
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
                'elevation': loc.get('elevation'),
                'population': loc.get('population')
            } for loc in results
        ],
        'count': len(results)
    }


def reverse_geocode(params):
    query_params = {
        'name': f"{params['lat']},{params['lon']}",
        'count': params['limit'],
        'language': params['language'],
        'format': 'json'
    }
    data = make_geocoding_request(query_params)
    results = data.get('results', [])
    if not results:
        return {'error': f"No location found near coordinates ({params['lat']}, {params['lon']})"}

    def distance(loc):
        lat_diff = abs(loc.get('latitude', 0) - params['lat'])
        lon_diff = abs(loc.get('longitude', 0) - params['lon'])
        return lat_diff + lon_diff

    sorted_results = sorted(results, key=distance)
    return {
        'coordinates': {'lat': params['lat'], 'lon': params['lon']},
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
            } for loc in sorted_results
        ],
        'count': len(sorted_results)
    }
