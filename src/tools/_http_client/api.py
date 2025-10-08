"""API routing layer for HTTP Client."""
from __future__ import annotations
from typing import Dict, Any

from .core import execute_request


def route_request(method: str, url: str, **params) -> Dict[str, Any]:
    """Route HTTP request to appropriate handler.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
        url: Target URL
        **params: Request parameters
        
    Returns:
        Response data or error
    """
    # All methods use the same handler (execute_request)
    # The method is passed through to requests library
    return execute_request(method, url, **params)
