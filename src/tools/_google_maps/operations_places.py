"""
Google Maps places operations
"""
import logging
from .services.api_client import make_request
from .formatters import format_place

logger = logging.getLogger(__name__)


def search_places(params):
    """Search for places by text query"""
    query_params = {
        'query': params['query'],
        'language': params['language']
    }
    
    logger.info(f"Searching places: {params['query']}")
    data = make_request('place/textsearch/json', query_params)
    
    results = data.get('results', [])
    limit = params['limit']
    total = len(results)
    returned = min(total, limit)
    
    result = {
        'query': params['query'],
        'results': [format_place(p) for p in results[:limit]],
        'total_count': total,
        'returned_count': returned
    }
    
    if total > limit:
        result['truncated'] = True
        result['message'] = f"Results truncated: {total} total, showing {returned}"
        logger.warning(f"Places search truncated: {total} → {returned}")
    
    return result


def get_place_details(params):
    """Get detailed information about a place"""
    query_params = {
        'place_id': params['place_id'],
        'language': params['language'],
        'fields': 'name,formatted_address,geometry,place_id,types,rating,user_ratings_total,opening_hours,formatted_phone_number,website,price_level,photos'
    }
    
    logger.info(f"Getting place details: {params['place_id']}")
    data = make_request('place/details/json', query_params)
    
    result = data.get('result', {})
    
    if not result:
        logger.warning(f"Place not found: {params['place_id']}")
        return {
            'error': f"Place '{params['place_id']}' not found"
        }
    
    return {
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
    
    logger.info(f"Searching nearby: ({params['lat']}, {params['lon']}) r={params['radius']}m")
    data = make_request('place/nearbysearch/json', query_params)
    
    results = data.get('results', [])
    limit = params['limit']
    total = len(results)
    returned = min(total, limit)
    
    result = {
        'coordinates': {
            'lat': params['lat'],
            'lon': params['lon']
        },
        'radius': params['radius'],
        'type': params.get('type'),
        'keyword': params.get('keyword'),
        'results': [format_place(p) for p in results[:limit]],
        'total_count': total,
        'returned_count': returned
    }
    
    if total > limit:
        result['truncated'] = True
        result['message'] = f"Results truncated: {total} total, showing {returned}"
        logger.warning(f"Nearby search truncated: {total} → {returned}")
    
    return result
