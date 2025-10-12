"""
HTTP client for image generation/editing API.
Simplified timeout management with environment variable overrides.
"""
from typing import Dict, Any, Tuple, Optional
import os
import requests


def build_headers(token: str) -> Dict[str, str]:
    """Build minimal headers to avoid 406 rejections."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _verify_ssl() -> bool:
    """Check if SSL verification is enabled (default: False in dev)."""
    v = os.getenv("LLM_VERIFY_SSL", "").strip().lower()
    if v == "":
        return False  # Default to False (dev parity with call_llm)
    return v not in ("0", "false", "no", "off")


def _get_int(name: str, default: int) -> int:
    """Safely parse integer from environment variable."""
    val = os.getenv(name, "").strip()
    if val == "":
        return default
    try:
        return int(val)
    except Exception:
        return default


def get_timeouts(is_multi_edit: bool = False) -> Tuple[int, int]:
    """
    Get (connect, read) timeouts for image operations.
    
    Defaults:
        - Single image: (15s, 180s)
        - Multi-edit (2+ images): (30s, 600s)
    
    Environment overrides:
        - IMAGE_TIMEOUT_SEC: read timeout for single operations
        - IMAGE_MULTI_TIMEOUT_SEC: read timeout for multi-edit
        - IMAGE_CONNECT_TIMEOUT_SEC: connect timeout (both modes)
    """
    connect_default = 15
    read_default = 180 if not is_multi_edit else 600
    
    connect = _get_int("IMAGE_CONNECT_TIMEOUT_SEC", connect_default)
    
    if is_multi_edit:
        read = _get_int("IMAGE_MULTI_TIMEOUT_SEC", read_default)
    else:
        read = _get_int("IMAGE_TIMEOUT_SEC", read_default)
    
    return (connect, read)


def post_stream(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeouts: Tuple[int, int]):
    """POST request with streaming response."""
    resp = requests.post(
        url,
        headers=headers,
        json=payload,
        stream=True,
        timeout=timeouts,
        verify=_verify_ssl(),
    )
    resp.raise_for_status()
    return resp


def post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeouts: Tuple[int, int]):
    """POST request with JSON response (no streaming)."""
    resp = requests.post(
        url,
        headers=headers,
        json=payload,
        stream=False,
        timeout=timeouts,
        verify=_verify_ssl(),
    )
    resp.raise_for_status()
    return resp
