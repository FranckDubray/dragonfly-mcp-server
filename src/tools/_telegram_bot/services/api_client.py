"""
Telegram Bot API client
"""
import os
import requests


def get_bot_token():
    """Get Telegram bot token from env"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN in .env")
    return token


def get_api_url(method):
    """Build Telegram API URL"""
    token = get_bot_token()
    return f"https://api.telegram.org/bot{token}/{method}"


def make_request(method, params=None, data=None, timeout=30):
    """
    Make request to Telegram Bot API
    
    Args:
        method: API method name (e.g., 'sendMessage', 'getUpdates')
        params: Query parameters dict
        POST data dict
        timeout: Request timeout in seconds
    
    Returns:
        Response result dict
    """
    url = get_api_url(method)
    
    try:
        if data:
            response = requests.post(url, json=data, timeout=timeout)
        else:
            response = requests.get(url, params=params, timeout=timeout)
        
        response.raise_for_status()
        result = response.json()
        
        if not result.get('ok'):
            error_code = result.get('error_code')
            description = result.get('description', 'Unknown error')
            
            # Provide helpful error messages
            if error_code == 400:
                raise ValueError(f"Bad request: {description}")
            elif error_code == 401:
                raise ValueError("Invalid TELEGRAM_BOT_TOKEN")
            elif error_code == 404:
                raise ValueError(f"Not found: {description}")
            elif error_code == 429:
                raise ValueError("Too many requests - rate limited")
            else:
                raise ValueError(f"API error ({error_code}): {description}")
        
        return result.get('result')
        
    except requests.exceptions.Timeout:
        raise ValueError(f"API request timeout ({timeout}s)")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"API request failed: {e}")
