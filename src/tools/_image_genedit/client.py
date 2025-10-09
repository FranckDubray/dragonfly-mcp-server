from typing import Dict, Any, Tuple, Optional
import os
import requests


def build_headers(token: str) -> Dict[str, str]:
    # Keep headers minimal to avoid 406
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _verify_ssl() -> bool:
    v = os.getenv("LLM_VERIFY_SSL", "").strip().lower()
    if v == "":
        # Default to False in DEV parity (same as call_llm)
        return False
    return v not in ("0", "false", "no", "off")


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name, "").strip()
    if val == "":
        return default
    try:
        return int(val)
    except Exception:
        return default


def _timeouts() -> Tuple[int, int]:
    """
    Timeouts specific to the image generation/editing tool.
    Precedence (highest to lowest):
      - IMAGE_CONNECT_TIMEOUT_SEC / IMAGE_REQUEST_TIMEOUT_SEC (per-tool override)
      - LLM_CONNECT_TIMEOUT_SEC / LLM_REQUEST_TIMEOUT_SEC (global)
      - Defaults: connect=15s, read=420s (longer by default for heavy multi-image edits)
    """
    # Defaults tuned for image composition workloads
    CONNECT_DEF = 15
    READ_DEF = 420

    # Per-tool overrides, falling back to global, then defaults
    connect = _get_int("IMAGE_CONNECT_TIMEOUT_SEC", _get_int("LLM_CONNECT_TIMEOUT_SEC", CONNECT_DEF))
    read = _get_int("IMAGE_REQUEST_TIMEOUT_SEC", _get_int("LLM_REQUEST_TIMEOUT_SEC", READ_DEF))
    return (connect, read)


def post_stream(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout_sec: int, timeouts_override: Optional[Tuple[int, int]] = None):
    # Ignore timeout_sec and use granular timeouts for reliability
    t = timeouts_override or _timeouts()
    resp = requests.post(
        url,
        headers=headers,
        json=payload,
        stream=True,
        timeout=t,
        verify=_verify_ssl(),
    )
    resp.raise_for_status()
    return resp


def post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout_sec: int, timeouts_override: Optional[Tuple[int, int]] = None):
    t = timeouts_override or _timeouts()
    resp = requests.post(
        url,
        headers=headers,
        json=payload,
        stream=False,
        timeout=t,
        verify=_verify_ssl(),
    )
    resp.raise_for_status()
    return resp
