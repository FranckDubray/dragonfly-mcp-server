"""
Core business logic for device location operations.
"""
from .services.ip_geolocation import get_location as get_ip_location


def get_device_location(provider='ipapi'):
    """
    Get current device location based on IP geolocation.
    
    Args:
        provider: Geolocation provider ('ipapi' or 'ip-api')
    
    Returns:
        dict: Location information with GPS coordinates and metadata
    """
    location = get_ip_location(provider)
    
    # Format response
    result = {
        'success': True,
        'provider': location['provider'],
        'coordinates': {
            'latitude': location['latitude'],
            'longitude': location['longitude'],
        },
        'location': {
            'city': location['city'],
            'region': location['region'],
            'region_code': location['region_code'],
            'country': location['country'],
            'country_code': location['country_code'],
            'continent': location['continent'],
            'postal': location['postal'],
        },
        'network': {
            'ip': location['ip'],
            'asn': location['asn'],
            'org': location['org'],
            'isp': location['isp'],
        },
        'timezone': {
            'name': location['timezone'],
            'utc_offset': location['utc_offset'],
        },
        'other': {
            'currency': location['currency'],
            'languages': location['languages'],
        }
    }
    
    # Remove None values for cleaner output
    result = _remove_none_values(result)
    
    return result


def _remove_none_values(d):
    """Recursively remove None values from dict."""
    if not isinstance(d, dict):
        return d
    return {
        k: _remove_none_values(v) 
        for k, v in d.items() 
        if v is not None and v != {}
    }
