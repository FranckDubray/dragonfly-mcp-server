"""
Core business logic for device location operations.
"""
import logging
from .services.system_location import get_system_location
from .services.ip_geolocation import get_location as get_ip_location

LOG = logging.getLogger(__name__)


def get_device_location(provider='ipapi'):
    """
    Get current device location with intelligent fallback:
    1. Try system GPS/WiFi (most accurate)
    2. Fall back to IP geolocation (least accurate)
    
    Args:
        provider: IP geolocation provider ('ipapi' or 'ip-api') - used as fallback
    
    Returns:
        dict: Location information with GPS coordinates and metadata
    """
    # Try system location first (GPS/WiFi)
    try:
        LOG.info("Attempting system location (GPS/WiFi)...")
        system_loc = get_system_location()
        
        result = {
            'success': True,
            'source': system_loc['source'],
            'method': 'system_api',
            'coordinates': {
                'latitude': system_loc['latitude'],
                'longitude': system_loc['longitude'],
            },
            'accuracy': {
                'horizontal_meters': system_loc.get('accuracy'),
                'note': 'Lower is better. <100m = good, <1000m = fair'
            }
        }
        
        if system_loc.get('altitude') is not None:
            result['coordinates']['altitude_meters'] = system_loc['altitude']
        
        LOG.info(f"✅ System location success: {system_loc['source']}")
        return result
        
    except Exception as e:
        LOG.warning(f"System location unavailable: {e}. Falling back to IP geolocation...")
    
    # Fallback: IP geolocation
    try:
        LOG.info(f"Using IP geolocation (provider: {provider})...")
        location = get_ip_location(provider)
        
        result = {
            'success': True,
            'source': f'IP Geolocation ({location["provider"]})',
            'method': 'ip_geolocation',
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
            },
            'accuracy': {
                'note': 'IP geolocation: city-level accuracy (~1-5 km radius)'
            }
        }
        
        # Remove None values
        result = _remove_none_values(result)
        
        LOG.info(f"✅ IP geolocation success: {location['provider']}")
        return result
        
    except Exception as ip_error:
        LOG.error(f"All location methods failed. IP error: {ip_error}")
        raise Exception(f"Unable to determine location: system location unavailable, IP geolocation failed ({ip_error})")


def _remove_none_values(d):
    """Recursively remove None values from dict."""
    if not isinstance(d, dict):
        return d
    return {
        k: _remove_none_values(v) 
        for k, v in d.items() 
        if v is not None and v != {}
    }
