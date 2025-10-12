"""
HTTP Client Tool - Universal REST/API client

Supports all HTTP methods (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS) with
authentication (Basic, Bearer, API Key), retry logic, timeout, proxy, and
intelligent response parsing.

Example:
  {
    "tool": "http_client",
    "params": {
      "method": "GET",
      "url": "https://api.github.com/users/octocat",
      "headers": {"Accept": "application/json"}
    }
  }
  
  {
    "tool": "http_client",
    "params": {
      "method": "POST",
      "url": "https://api.example.com/data",
      "json": {"name": "test", "value": 42},
      "auth_type": "bearer",
      "auth_token": "your_token_here"
    }
  }
"""
from __future__ import annotations
from typing import Dict, Any

from ._http_client.api import route_request
from ._http_client import spec as _spec


def run(**params) -> Dict[str, Any]:
    """Execute HTTP request.
    
    Args:
        **params: Request parameters (method, url, headers, body, auth, etc.)
        
    Returns:
        Response with status, headers, body
    """
    # Extract method and url from params
    method = params.get("method", "GET")
    url = params.get("url")
    
    # Normalize method
    if method:
        method = str(method).strip().upper()
    else:
        method = "GET"
    
    # Validate required params
    if not url:
        return {"error": "Parameter 'url' is required"}
    
    # Validate method
    valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    if method not in valid_methods:
        return {"error": f"Invalid method '{method}'. Must be one of: {', '.join(valid_methods)}"}
    
    # Remove method and url from params to avoid duplicate arguments
    clean_params = {k: v for k, v in params.items() if k not in ("method", "url")}
    
    # Route to handler
    return route_request(method, url, **clean_params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    return _spec()
