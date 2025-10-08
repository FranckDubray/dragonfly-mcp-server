"""Input validation for HTTP Client."""
from __future__ import annotations
from typing import Dict, Any
from urllib.parse import urlparse


def validate_url(url: str) -> Dict[str, Any]:
    """Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        Dict with 'valid' (bool) and optional 'error' (str)
    """
    if not url or not isinstance(url, str):
        return {"valid": False, "error": "URL must be a non-empty string"}
    
    url = url.strip()
    
    if not url:
        return {"valid": False, "error": "URL cannot be empty"}
    
    try:
        parsed = urlparse(url)
        
        if parsed.scheme not in ["http", "https"]:
            return {"valid": False, "error": "URL must use http or https scheme"}
        
        if not parsed.netloc:
            return {"valid": False, "error": "URL must have a valid domain"}
        
        return {"valid": True, "url": url}
        
    except Exception as e:
        return {"valid": False, "error": f"Invalid URL format: {str(e)}"}


def validate_timeout(timeout: Any) -> Dict[str, Any]:
    """Validate timeout value.
    
    Args:
        timeout: Timeout value
        
    Returns:
        Dict with 'valid' (bool), 'timeout' (int), and optional 'error'
    """
    if timeout is None:
        return {"valid": True, "timeout": 30}  # Default
    
    try:
        timeout = int(timeout)
        
        if timeout < 1:
            return {"valid": False, "error": "Timeout must be at least 1 second"}
        
        if timeout > 600:
            return {"valid": False, "error": "Timeout cannot exceed 600 seconds"}
        
        return {"valid": True, "timeout": timeout}
        
    except (ValueError, TypeError):
        return {"valid": False, "error": "Timeout must be an integer"}


def validate_proxy(proxy: str) -> Dict[str, Any]:
    """Validate proxy URL.
    
    Args:
        proxy: Proxy URL
        
    Returns:
        Dict with 'valid' (bool) and optional 'error'
    """
    if not proxy:
        return {"valid": True, "proxy": None}
    
    if not isinstance(proxy, str):
        return {"valid": False, "error": "Proxy must be a string"}
    
    proxy = proxy.strip()
    
    try:
        parsed = urlparse(proxy)
        
        if parsed.scheme not in ["http", "https", "socks5"]:
            return {"valid": False, "error": "Proxy must use http, https, or socks5 scheme"}
        
        if not parsed.netloc:
            return {"valid": False, "error": "Proxy must have a valid domain"}
        
        return {"valid": True, "proxy": proxy}
        
    except Exception as e:
        return {"valid": False, "error": f"Invalid proxy format: {str(e)}"}


def validate_max_retries(max_retries: Any) -> Dict[str, Any]:
    """Validate max_retries value.
    
    Args:
        max_retries: Max retries value
        
    Returns:
        Dict with 'valid' (bool), 'max_retries' (int), and optional 'error'
    """
    if max_retries is None:
        return {"valid": True, "max_retries": 0}  # Default
    
    try:
        max_retries = int(max_retries)
        
        if max_retries < 0:
            return {"valid": False, "error": "max_retries cannot be negative"}
        
        if max_retries > 5:
            return {"valid": False, "error": "max_retries cannot exceed 5"}
        
        return {"valid": True, "max_retries": max_retries}
        
    except (ValueError, TypeError):
        return {"valid": False, "error": "max_retries must be an integer"}


def validate_retry_delay(retry_delay: Any) -> Dict[str, Any]:
    """Validate retry_delay value.
    
    Args:
        retry_delay: Retry delay value
        
    Returns:
        Dict with 'valid' (bool), 'retry_delay' (float), and optional 'error'
    """
    if retry_delay is None:
        return {"valid": True, "retry_delay": 1.0}  # Default
    
    try:
        retry_delay = float(retry_delay)
        
        if retry_delay < 0.1:
            return {"valid": False, "error": "retry_delay must be at least 0.1 seconds"}
        
        if retry_delay > 10.0:
            return {"valid": False, "error": "retry_delay cannot exceed 10 seconds"}
        
        return {"valid": True, "retry_delay": retry_delay}
        
    except (ValueError, TypeError):
        return {"valid": False, "error": "retry_delay must be a number"}
