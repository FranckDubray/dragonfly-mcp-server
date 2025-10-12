"""
Google Maps routing operations (directions, distance_matrix)
"""
import logging
from .services.api_client import make_request
from .formatters import format_route

logger = logging.getLogger(__name__)


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
    
    logger.info(f"Getting directions: {params['origin']} → {params['destination']} ({params['mode']})")
    data = make_request('directions/json', query_params)
    
    routes = data.get('routes', [])
    
    if not routes:
        logger.warning(f"No route found: {params['origin']} → {params['destination']}")
        return {
            'error': 'No route found between origin and destination'
        }
    
    return {
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
    
    logger.info(f"Distance matrix: {len(params['origins'])} origins × {len(params['destinations'])} destinations")
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
        'mode': params['mode'],
        'matrix': matrix,
        'total_combinations': len(matrix)
    }
