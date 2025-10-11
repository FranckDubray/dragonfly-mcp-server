"""
Google Maps core business logic
"""
from .services.api_client import make_request
from .utils import format_location, format_route, format_place


def geocode_address(params):
    """Convert address to coordinates"""
    query_params = {
        'address': params['address'],
        'language': params['language']
    }
    
    data = make_request('geocode/json', query_params)
    
    results = data.get('results', [])
    
    if not results:
        return {
            'success': False,
            'error': f"Address '{params['address']}' not found"
        }
    
    return {
        'success': True,
        'operation': 'geocode',
        'query': params['address'],
        'results': [format_location(r) for r in results[:params['limit']]],
        'returned_count': len(results[:params['limit']])
    }


def reverse_geocode_coords(params):
    """Convert coordinates to address"""
    query_params = {
        'latlng': f"{params['lat']},{params['lon']}",
        'language': params['language']
    }
    
    data = make_request('geocode/json', query_params)
    
    results = data.get('results', [])
    
    if not results:
        return {
            'success': False,
            'error': f"No address found for coordinates ({params['lat']}, {params['lon']})"
        }
    
    return {
        'success': True,
        'operation': 'reverse_geocode',
        'coordinates': {
            'lat': params['lat'],
            'lon': params['lon']
        },
        'results': [format_location(r) for r in results[:params['limit']]],
        'returned_count': len(results[:params['limit']])
    }


def get_directions(params):
    """Get directions between origin and destination"""
    query_params = {
        'origin': params['origin'],
        'destination': params['destination'],
        'mode': params['mode'],
        'language': params['language'],
        'alternatives': str(params['alternatives']).lower()
    }
    
    # Add optional params
    if params.get('avoid'):
        query_params['avoid'] = '|'.join(params['avoid'])
    
    if params.get('departure_time'):
        query_params['departure_time'] = params['departure_time']
    
    if params.get('arrival_time'):
        query_params['arrival_time'] = params['arrival_time']
    
    data = make_request('directions/json', query_params)
    
    routes = data.get('routes', [])
    
    if not routes:
        return {
            'success': False,
            'error': 'No route found between origin and destination'
        }
    
    return {
        'success': True,
        'operation': 'directions',
        'origin': params['origin'],
        'destination': params['destination'],
        'mode': params['mode'],
        'routes': [format_route(r) for r in routes],
        'routes_count': len(routes)
    }


def get_distance_matrix(params):
    """Get distances and durations between multiple origins and destinations"""
    query_params = {
        'origins': '|'.join(params['origins']),
        'destinations': '|'.join(params['destinations']),
        'mode': params['mode'],
        'language': params['language']
    }
    
    # Add optional params
    if params.get('avoid'):
        query_params['avoid'] = '|'.join(params['avoid'])
    
    if params.get('departure_time'):
        query_params['departure_time'] = params['departure_time']
    
    data = make_request('distancematrix/json', query_params)
    
    rows = data.get('rows', [])
    
    # Format matrix
    matrix = []
    for i, row in enumerate(rows):
        for j, element in enumerate(row.get('elements', [])):
            origin = params['origins'][i] if i < len(params['origins']) else 'Unknown'
            destination = params['destinations'][j] if j < len(params['destinations']) else 'Unknown'
            
            if element.get('status') == 'OK':
                matrix.append({
                    'origin': origin,
                    'destination': destination,
                    'distance': {
                        'meters': element.get('distance', {}).get('value'),
                        'text': element.get('distance', {}).get('text')
                    },
                    'duration': {
                        'seconds': element.get('duration', {}).get('value'),
                        'text': element.get('duration', {}).get('text')
                    },
                    'duration_in_traffic': {
                        'seconds': element.get('duration_in_traffic', {}).get('value'),
                        'text': element.get('duration_in_traffic', {}).get('text')
                    } if 'duration_in_traffic' in element else None
                })
            else:
                matrix.append({
                    'origin': origin,
                    'destination': destination,
                    'error': element.get('status')
                })
    
    return {
        'success': True,
        'operation': 'distance_matrix',
        'mode': params['mode'],
        'matrix': matrix,
        'total_combinations': len(matrix)
    }


def search_places(params):
    """Search for places by text query"""
    query_params = {
        'query': params['query'],
        'language': params['language']
    }
    
    data = make_request('place/textsearch/json', query_params)
    
    results = data.get('results', [])
    
    return {
        'success': True,
        'operation': 'places_search',
        'query': params['query'],
        'results': [format_place(p) for p in results[:params['limit']]],
        'returned_count': len(results[:params['limit']]),
        'truncated': len(results) > params['limit']
    }


def get_place_details(params):
    """Get detailed information about a place"""
    query_params = {
        'place_id': params['place_id'],
        'language': params['language'],
        'fields': 'name,formatted_address,geometry,place_id,types,rating,user_ratings_total,opening_hours,formatted_phone_number,website,price_level,photos'
    }
    
    data = make_request('place/details/json', query_params)
    
    result = data.get('result', {})
    
    if not result:
        return {
            'success': False,
            'error': f"Place '{params['place_id']}' not found"
        }
    
    return {
        'success': True,
        'operation': 'place_details',
        'place_id': params['place_id'],
        'details': format_place(result, detailed=True)
    }


def search_nearby_places(params):
    """Search for places nearby coordinates"""
    query_params = {
        'location': f"{params['lat']},{params['lon']}",
        'radius': params['radius'],
        'language': params['language']
    }
    
    # Add optional filters
    if params.get('type'):
        query_params['type'] = params['type']
    
    if params.get('keyword'):
        query_params['keyword'] = params['keyword']
    
    data = make_request('place/nearbysearch/json', query_params)
    
    results = data.get('results', [])
    
    return {
        'success': True,
        'operation': 'places_nearby',
        'coordinates': {
            'lat': params['lat'],
            'lon': params['lon']
        },
        'radius': params['radius'],
        'type': params.get('type'),
        'keyword': params.get('keyword'),
        'results': [format_place(p) for p in results[:params['limit']]],
        'returned_count': len(results[:params['limit']]),
        'truncated': len(results) > params['limit']
    }


def get_timezone(params):
    """Get timezone for coordinates"""
    import time
    
    query_params = {
        'location': f"{params['lat']},{params['lon']}",
        'timestamp': int(time.time())
    }
    
    data = make_request('timezone/json', query_params)
    
    return {
        'success': True,
        'operation': 'timezone',
        'coordinates': {
            'lat': params['lat'],
            'lon': params['lon']
        },
        'timezone_id': data.get('timeZoneId'),
        'timezone_name': data.get('timeZoneName'),
        'raw_offset': data.get('rawOffset'),
        'dst_offset': data.get('dstOffset')
    }


def get_elevation(params):
    """Get elevation for coordinates"""
    query_params = {
        'locations': f"{params['lat']},{params['lon']}"
    }
    
    data = make_request('elevation/json', query_params)
    
    results = data.get('results', [])
    
    if not results:
        return {
            'success': False,
            'error': 'No elevation data available'
        }
    
    result = results[0]
    
    return {
        'success': True,
        'operation': 'elevation',
        'coordinates': {
            'lat': result.get('location', {}).get('lat'),
            'lon': result.get('location', {}).get('lng')
        },
        'elevation': result.get('elevation'),
        'resolution': result.get('resolution')
    }
