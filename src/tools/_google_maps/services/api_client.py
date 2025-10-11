"""
Google Maps API client with fallback token logic
"""
import os
import requests


BASE_URL = 'https://maps.googleapis.com/maps/api'


def get_api_key():
    """
    Get Google Maps API key with fallback logic
    
    Priority:
    1. GOOGLE_MAPS_API_KEY (specific)
    2. GOOGLE_API_KEY (generic fallback)
    
    Returns:
        API key string
    
    Raises:
        ValueError if no key found
    """
    # Try specific key first
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if api_key:
        return api_key
    
    # Fallback to generic Google key
    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key:
        return api_key
    
    raise ValueError(
        "Missing Google API token. Set either GOOGLE_MAPS_API_KEY or GOOGLE_API_KEY in .env"
    )


def make_request(endpoint, params=None):
    """
    Make request to Google Maps API
    
    Args:
        endpoint: API endpoint (e.g., 'geocode/json', 'directions/json')
        params: Query parameters dict
    
    Returns:
        Response JSON dict
    """
    api_key = get_api_key()
    
    # Build URL
    url = f"{BASE_URL}/{endpoint}"
    
    # Add API key to params
    request_params = params.copy() if params else {}
    request_params['key'] = api_key
    
    # Make request
    try:
        response = requests.get(url, params=request_params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Check API status
        status = data.get('status')
        if status == 'OK' or status == 'ZERO_RESULTS':
            return data
        elif status == 'REQUEST_DENIED':
            error_msg = data.get('error_message', 'API key invalid or not authorized for this service')
            raise ValueError(f"API request denied: {error_msg}")
        elif status == 'INVALID_REQUEST':
            error_msg = data.get('error_message', 'Invalid request parameters')
            raise ValueError(f"Invalid request: {error_msg}")
        elif status == 'OVER_QUERY_LIMIT':
            raise ValueError("API quota exceeded")
        elif status == 'UNKNOWN_ERROR':
            raise ValueError("Google Maps API error (retry later)")
        else:
            raise ValueError(f"API error: {status}")
            
    except requests.exceptions.Timeout:
        raise ValueError("API request timeout")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"API request failed: {e}")
