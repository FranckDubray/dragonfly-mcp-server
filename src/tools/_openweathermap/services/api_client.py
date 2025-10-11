"""
OpenWeatherMap API client
"""
import os
import requests


BASE_URL = 'https://api.openweathermap.org'


def get_api_key():
    """Get OpenWeatherMap API key from env"""
    api_key = os.getenv('OPENWEATHERMAP_API_KEY')
    if not api_key:
        raise ValueError("Missing OPENWEATHERMAP_API_KEY in .env")
    return api_key


def make_request(endpoint, params=None, version='2.5'):
    """
    Make request to OpenWeatherMap API
    
    Args:
        endpoint: API endpoint (e.g., 'weather', 'forecast', 'air_pollution')
        params: Query parameters dict
        version: API version (default: 2.5)
    
    Returns:
        Response JSON dict
    """
    api_key = get_api_key()
    
    # Build URL
    url = f"{BASE_URL}/data/{version}/{endpoint}"
    
    # Add API key to params
    request_params = params.copy() if params else {}
    request_params['appid'] = api_key
    
    # Make request
    try:
        response = requests.get(url, params=request_params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            raise ValueError("Invalid OPENWEATHERMAP_API_KEY")
        elif response.status_code == 404:
            raise ValueError("Location not found")
        elif response.status_code == 429:
            raise ValueError("API rate limit exceeded (60 calls/min)")
        else:
            raise ValueError(f"API error: {e}")
    except requests.exceptions.Timeout:
        raise ValueError("API request timeout")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"API request failed: {e}")


def make_geo_request(endpoint, params=None):
    """Make request to Geocoding API"""
    api_key = get_api_key()
    
    url = f"{BASE_URL}/geo/1.0/{endpoint}"
    
    request_params = params.copy() if params else {}
    request_params['appid'] = api_key
    
    try:
        response = requests.get(url, params=request_params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Geocoding API error: {e}")
