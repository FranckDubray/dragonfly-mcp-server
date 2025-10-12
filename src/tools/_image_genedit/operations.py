"""
Image API operations: single calls and sequential fallback.
Extracted from core.py to keep files under 7KB limit.
"""
from typing import Any, Dict, List, Tuple
import requests

from .client import build_headers, post_stream, post_json
from .streaming import process_stream_for_images
from .payloads import build_payload
from .utils import extract_image_urls


def _single_call(
    endpoint: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeouts: Tuple[int, int]
) -> Dict[str, Any]:
    """
    Execute a single API call and extract image URLs.
    Tries non-stream first, then falls back to streaming if needed.
    """
    # Try non-stream first (some backends reject streaming for images)
    try:
        payload_no_stream = dict(payload)
        payload_no_stream["stream"] = False
        resp = post_json(endpoint, headers, payload_no_stream, timeouts)
        j = resp.json()
        http_urls: List[str] = []
        
        if isinstance(j, dict):
            # 1) Standard content list (image_url)
            for ch in (j.get("choices") or []):
                msg = (ch.get("message") or {})
                content = msg.get("content")
                if isinstance(content, list):
                    for it in content:
                        if isinstance(it, dict) and it.get("type") == "image_url":
                            u = ((it.get("image_url") or {}).get("url"))
                            if isinstance(u, str) and u.startswith("http"):
                                http_urls.append(u)
            
            # 2) Provider sometimes gives an <img src="https://..."></img> tag
            if not http_urls:
                text = "".join([(c.get("delta", {}).get("content") or "") for c in (j.get("choices") or [])])
                if isinstance(text, str) and text:
                    http_urls.extend(extract_image_urls(text))
            
            if http_urls:
                # Dedupe preserving order
                seen = set()
                http_urls = [u for u in http_urls if not (u in seen or seen.add(u))]
                return {
                    "urls": http_urls,
                    "finish_reason": "stop",
                    "usage": j.get("usage") if isinstance(j, dict) else None,
                    "raw_preview": [],
                }
    except Exception:
        pass
    
    # Fallback to streaming
    payload_stream = dict(payload)
    payload_stream["stream"] = True
    resp = post_stream(endpoint, headers, payload_stream, timeouts)
    res = process_stream_for_images(resp)
    
    # Extract http(s) URLs from SSE + text content
    http_urls: List[str] = []
    for u in (res.get("http_urls") or []):
        if isinstance(u, str) and u.startswith("http"):
            http_urls.append(u)
    if isinstance(res.get("text"), str) and res["text"]:
        http_urls.extend(extract_image_urls(res["text"]))
    
    # Dedupe
    seen = set()
    http_urls = [u for u in http_urls if not (u in seen or seen.add(u))]
    
    return {
        "urls": http_urls,
        "finish_reason": res.get("finish_reason"),
        "usage": res.get("usage"),
        "raw_preview": res.get("raw_preview"),
    }


def _sequential_fallback(
    endpoint: str,
    headers: Dict[str, str],
    messages: List[Dict[str, Any]],
    n: int,
    model: str,
    timeouts: Tuple[int, int]
) -> Dict[str, Any]:
    """
    Execute n separate single-image calls when batch fails.
    Aggregates URLs and usage across all calls.
    """
    all_urls: List[str] = []
    all_usages: List[Dict[str, Any]] = []
    
    for _ in range(n):
        payload = build_payload(messages, 1, model)
        payload.pop("n", None)  # Remove n parameter for single calls
        
        try:
            result = _single_call(endpoint, headers, payload, timeouts)
            urls = result.get("urls", []) or []
            all_urls.extend(urls)
            
            if result.get("usage"):
                all_usages.append(result["usage"])
        except Exception:
            continue
    
    # Aggregate usage
    usage_agg: Dict[str, Any] = {}
    for u in all_usages:
        for k, v in u.items():
            if isinstance(v, (int, float)):
                usage_agg[k] = usage_agg.get(k, 0) + v
    
    return {
        "urls": all_urls,
        "usage": usage_agg or None,
        "finish_reason": "stop",
    }
