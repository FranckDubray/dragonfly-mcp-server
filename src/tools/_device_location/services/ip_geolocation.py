"""
IP-based geolocation services.
Supports multiple providers for redundancy.
"""
import requests
import logging

LOG = logging.getLogger(__name__)


def get_location_ipapi():
    """
    Get location using ipapi.co (free, no API key).
    Returns detailed location info.
    """
    try:
        response = requests.get('https://ipapi.co/json/', timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            'provider': 'ipapi.co',
            'ip': data.get('ip'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'city': data.get('city'),
            'region': data.get('region'),
            'region_code': data.get('region_code'),
            'country': data.get('country_name'),
            'country_code': data.get('country_code'),
            'continent': data.get('continent_code'),
            'postal': data.get('postal'),
            'timezone': data.get('timezone'),
            'utc_offset': data.get('utc_offset'),
            'currency': data.get('currency'),
            'languages': data.get('languages'),
            'asn': data.get('asn'),
            'org': data.get('org'),
            'isp': data.get('org'),  # Same as org for ipapi
        }
    except Exception as e:
        LOG.error(f"ipapi.co request failed: {e}")
        raise


def get_location_ip_api():
    """
    Get location using ip-api.com (free, no API key, rate limit 45 req/min).
    Returns detailed location info.
    """
    try:
        response = requests.get('http://ip-api.com/json/', timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') != 'success':
            raise Exception(f"ip-api.com returned status: {data.get('status')}, message: {data.get('message')}")
        
        return {
            'provider': 'ip-api.com',
            'ip': data.get('query'),
            'latitude': data.get('lat'),
            'longitude': data.get('lon'),
            'city': data.get('city'),
            'region': data.get('regionName'),
            'region_code': data.get('region'),
            'country': data.get('country'),
            'country_code': data.get('countryCode'),
            'continent': None,  # Not provided by ip-api
            'postal': data.get('zip'),
            'timezone': data.get('timezone'),
            'utc_offset': None,  # Not provided by ip-api
            'currency': None,  # Not provided by ip-api
            'languages': None,  # Not provided by ip-api
            'asn': data.get('as'),
            'org': data.get('org'),
            'isp': data.get('isp'),
        }
    except Exception as e:
        LOG.error(f"ip-api.com request failed: {e}")
        raise


def get_location(provider='ipapi'):
    """
    Get device location using specified provider.
    Falls back to alternative provider on failure.
    """
    providers = {
        'ipapi': get_location_ipapi,
        'ip-api': get_location_ip_api,
    }
    
    primary = providers.get(provider, get_location_ipapi)
    
    try:
        return primary()
    except Exception as e:
        LOG.warning(f"Primary provider {provider} failed: {e}. Trying fallback...")
        # Try fallback provider
        fallback = get_location_ip_api if provider == 'ipapi' else get_location_ipapi
        try:
            return fallback()
        except Exception as fallback_error:
            raise Exception(f"All geolocation providers failed. Last error: {fallback_error}")
