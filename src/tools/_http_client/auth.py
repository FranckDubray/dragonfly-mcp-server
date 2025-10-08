"""Authentication helpers for HTTP Client."""
from __future__ import annotations
from typing import Dict, Any, Optional, Tuple
import base64


def build_auth_headers(
    auth_type: Optional[str] = None,
    auth_user: Optional[str] = None,
    auth_password: Optional[str] = None,
    auth_token: Optional[str] = None,
    auth_api_key_name: Optional[str] = None,
    auth_api_key_value: Optional[str] = None
) -> Dict[str, str]:
    """Build authentication headers.
    
    Args:
        auth_type: Type of auth (basic, bearer, api_key, none)
        auth_user: Username for Basic Auth
        auth_password: Password for Basic Auth
        auth_token: Token for Bearer Auth
        auth_api_key_name: API Key header name
        auth_api_key_value: API Key value
        
    Returns:
        Dict of headers to add
    """
    headers = {}
    
    if not auth_type or auth_type == "none":
        return headers
    
    auth_type = auth_type.lower().strip()
    
    if auth_type == "basic":
        if auth_user and auth_password:
            credentials = f"{auth_user}:{auth_password}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
    
    elif auth_type == "bearer":
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
    
    elif auth_type == "api_key":
        if auth_api_key_name and auth_api_key_value:
            headers[auth_api_key_name] = auth_api_key_value
    
    return headers


def validate_auth_params(
    auth_type: Optional[str] = None,
    auth_user: Optional[str] = None,
    auth_password: Optional[str] = None,
    auth_token: Optional[str] = None,
    auth_api_key_name: Optional[str] = None,
    auth_api_key_value: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Validate authentication parameters.
    
    Args:
        auth_type: Type of auth
        auth_user: Username for Basic Auth
        auth_password: Password for Basic Auth
        auth_token: Token for Bearer Auth
        auth_api_key_name: API Key header name
        auth_api_key_value: API Key value
        
    Returns:
        Tuple of (valid: bool, error: Optional[str])
    """
    if not auth_type or auth_type == "none":
        return True, None
    
    auth_type = auth_type.lower().strip()
    
    if auth_type not in ["basic", "bearer", "api_key", "none"]:
        return False, f"Invalid auth_type '{auth_type}'. Must be: basic, bearer, api_key, or none"
    
    if auth_type == "basic":
        if not auth_user or not auth_password:
            return False, "Basic auth requires both auth_user and auth_password"
    
    elif auth_type == "bearer":
        if not auth_token:
            return False, "Bearer auth requires auth_token"
    
    elif auth_type == "api_key":
        if not auth_api_key_name or not auth_api_key_value:
            return False, "API Key auth requires both auth_api_key_name and auth_api_key_value"
    
    return True, None
