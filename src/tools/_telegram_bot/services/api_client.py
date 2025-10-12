"""
Telegram Bot API client
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)


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


def mask_url(url):
    """Mask bot token in URL for logging/errors"""
    # Replace token part (between /bot and /)
    if '/bot' in url:
        parts = url.split('/bot')
        if len(parts) >= 2:
            rest = parts[1].split('/', 1)
            if len(rest) >= 2:
                return f"{parts[0]}/bot***TOKEN_MASKED***/{rest[1]}"
    return url


def make_request(method, params=None, data=None, timeout=30):
    """
    Make request to Telegram Bot API
    
    Args:
        method: API method name (e.g., 'sendMessage', 'getUpdates')
        params: Query parameters dict
        data: POST data dict
        timeout: Request timeout in seconds
    
    Returns:
        Response result dict
    """
    url = get_api_url(method)
    
    logger.info(f"Telegram API call: {method} (timeout={timeout}s)")
    
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
            
            logger.warning(f"Telegram API error {error_code}: {description}")
            
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
        logger.warning(f"Telegram API timeout ({timeout}s)")
        raise ValueError(f"API request timeout ({timeout}s)")
    except requests.exceptions.RequestException as e:
        # SECURITY: Mask token in error messages
        safe_url = mask_url(url)
        error_msg = str(e).replace(url, safe_url)
        logger.error(f"Telegram API request failed: {error_msg}")
        raise ValueError(f"API request failed: {error_msg}")
