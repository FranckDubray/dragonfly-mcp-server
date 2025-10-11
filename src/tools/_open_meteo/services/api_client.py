"""
Open-Meteo API client (no API key required - 100% free)
"""
import requests


FORECAST_BASE_URL = 'https://api.open-meteo.com/v1'
AIR_QUALITY_BASE_URL = 'https://air-quality-api.open-meteo.com/v1'
GEOCODING_BASE_URL = 'https://geocoding-api.open-meteo.com/v1'


def make_forecast_request(params):
    """
    Make request to Open-Meteo Forecast API
    
    Args:
        params: Query parameters dict
    
    Returns:
        Response JSON dict
    """
    url = f"{FORECAST_BASE_URL}/forecast"
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            raise ValueError(f"Invalid request parameters: {response.text}")
        elif response.status_code == 429:
            raise ValueError("API rate limit exceeded (retry after a few seconds)")
        else:
            raise ValueError(f"API error: {e}")
    except requests.exceptions.Timeout:
        raise ValueError("API request timeout")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"API request failed: {e}")


def make_air_quality_request(params):
    """
    Make request to Open-Meteo Air Quality API
    
    Args:
        params: Query parameters dict
    
    Returns:
        Response JSON dict
    """
    url = f"{AIR_QUALITY_BASE_URL}/air-quality"
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Air quality API error: {e}")


def make_geocoding_request(params):
    """
    Make request to Open-Meteo Geocoding API
    
    Args:
        params: Query parameters dict
    
    Returns:
        Response JSON dict
    """
    url = f"{GEOCODING_BASE_URL}/search"
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Geocoding API error: {e}")
