from __future__ import annotations
import os
import requests
from typing import Any, Dict
import urllib3


# Disable SSL warnings only when SSL verification is disabled
def _should_verify_ssl() -> bool:
    """Check if SSL verification should be enabled (default: True in production)."""
    verify = os.getenv("LLM_VERIFY_SSL", "true").lower()
    return verify in ("true", "1", "yes", "on")


# Suppress warnings only when SSL verification is disabled
if not _should_verify_ssl():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def build_headers(token: str) -> Dict[str, str]:
    """Build HTTP headers with authorization token."""
    return {
        "Authorization": f"Bearer {token}", 
        "Content-Type": "application/json"
    }


def post_stream(endpoint: str, headers: Dict[str, str], json_payload: Dict[str, Any], timeout_sec: int):
    """
    POST request with streaming support and configurable SSL verification.
    
    SSL verification controlled by LLM_VERIFY_SSL environment variable:
    - "true" (default): Verify SSL certificates (recommended for production)
    - "false": Disable SSL verification (dev/testing only)
    """
    verify_ssl = _should_verify_ssl()
    
    return requests.post(
        endpoint, 
        headers=headers, 
        json=json_payload, 
        stream=True, 
        timeout=timeout_sec, 
        verify=verify_ssl
    )
