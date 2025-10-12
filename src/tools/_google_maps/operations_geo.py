"""
Google Maps geocoding operations
"""
import logging
from .services.api_client import make_request
from .formatters import format_location

logger = logging.getLogger(__name__)


def geocode_address(params):
    """Convert address to coordinates"""
    query_params = {
        'address': params['address'],
        'language': params['language']
    }
    
    logger.info(f"Geocoding address: {params['address']}")
    data = make_request('geocode/json', query_params)
    
    results = data.get('results', [])
    
    if not results:
        logger.warning(f"Address not found: {params['address']}")
        return {
            'error': f"Address '{params['address']}' not found"
        }
    
    limit = params['limit']
    total = len(results)
    returned = min(total, limit)
    
    result = {
        'query': params['address'],
        'results': [format_location(r) for r in results[:limit]],
        'total_count': total,
        'returned_count': returned
    }
    
    if total > limit:
        result['truncated'] = True
        result['message'] = f"Results truncated: {total} total, showing {returned}"
        logger.warning(f"Geocode results truncated: {total} → {returned}")
    
    return result


def reverse_geocode_coords(params):
    """Convert coordinates to address"""
    query_params = {
        'latlng': f"{params['lat']},{params['lon']}",
        'language': params['language']
    }
    
    logger.info(f"Reverse geocoding: ({params['lat']}, {params['lon']})")
    data = make_request('geocode/json', query_params)
    
    results = data.get('results', [])
    
    if not results:
        logger.warning(f"No address found for: ({params['lat']}, {params['lon']})")
        return {
            'error': f"No address found for coordinates ({params['lat']}, {params['lon']})"
        }
    
    limit = params['limit']
    total = len(results)
    returned = min(total, limit)
    
    result = {
        'coordinates': {
            'lat': params['lat'],
            'lon': params['lon']
        },
        'results': [format_location(r) for r in results[:limit]],
        'total_count': total,
        'returned_count': returned
    }
    
    if total > limit:
        result['truncated'] = True
        result['message'] = f"Results truncated: {total} total, showing {returned}"
        logger.warning(f"Reverse geocode results truncated: {total} → {returned}")
    
    return result


def get_timezone(params):
    """Get timezone for coordinates"""
    import time
    
    query_params = {
        'location': f"{params['lat']},{params['lon']}",
        'timestamp': int(time.time())
    }
    
    logger.info(f"Getting timezone: ({params['lat']}, {params['lon']})")
    data = make_request('timezone/json', query_params)
    
    return {
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
    
    logger.info(f"Getting elevation: ({params['lat']}, {params['lon']})")
    data = make_request('elevation/json', query_params)
    
    results = data.get('results', [])
    
    if not results:
        logger.warning(f"No elevation ({params['lat']}, {params['lon']})")
        return {
            'error': 'No elevation data available'
        }
    
    result = results[0]
    
    return {
        'coordinates': {
            'lat': result.get('location', {}).get('lat'),
            'lon': result.get('location', {}).get('lng')
        },
        'elevation': result.get('elevation'),
        'resolution': result.get('resolution')
    }
