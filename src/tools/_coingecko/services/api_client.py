"""
CoinGecko API client (no API key required for free tier)
"""
import requests


BASE_URL = 'https://api.coingecko.com/api/v3'


def make_request(endpoint, params=None):
    """
    Make request to CoinGecko API
    
    Args:
        endpoint: API endpoint (e.g., 'simple/price', 'coins/bitcoin')
        params: Query parameters dict
    
    Returns:
        Response JSON dict or list
    """
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            raise ValueError("Coin or resource not found")
        elif response.status_code == 429:
            raise ValueError("API rate limit exceeded (50 calls/min)")
        else:
            raise ValueError(f"API error: {e}")
    except requests.exceptions.Timeout:
        raise ValueError("API request timeout")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"API request failed: {e}")
