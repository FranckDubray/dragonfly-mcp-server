"""Retry logic with exponential backoff for HTTP Client."""
from __future__ import annotations
from typing import Callable, Any, Dict
import time


def retry_with_backoff(
    func: Callable,
    max_retries: int = 0,
    retry_delay: float = 1.0,
    exponential: bool = True
) -> Any:
    """Retry a function with exponential backoff.
    
    Args:
        func: Function to retry (must be callable)
        max_retries: Maximum number of retries
        retry_delay: Base delay between retries (seconds)
        exponential: Use exponential backoff (2^attempt * delay)
        
    Returns:
        Function result or raises last exception
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            # Don't retry on last attempt
            if attempt == max_retries:
                break
            
            # Calculate delay
            if exponential:
                delay = retry_delay * (2 ** attempt)
            else:
                delay = retry_delay
            
            # Sleep before retry
            time.sleep(delay)
    
    # Re-raise last exception
    raise last_exception


def should_retry(response_status: int) -> bool:
    """Determine if a response should be retried.
    
    Args:
        response_status: HTTP status code
        
    Returns:
        True if should retry
    """
    # Retry on server errors (5xx) and some client errors
    retry_status_codes = [
        408,  # Request Timeout
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
    ]
    
    return response_status in retry_status_codes
