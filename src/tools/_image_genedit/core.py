"""
Core image generation/editing logic.
Simplified with proper fallback handling and minimal duplication.
"""
from typing import Any, Dict, List, Optional, Tuple
import os
import requests

from .client import build_headers, post_stream, post_json, get_timeouts
from .streaming import process_stream_for_images
from .payloads import DEFAULT_N, build_messages_for_generate, build_messages_for_edit, build_payload
from .utils import extract_image_urls


MODEL = "gemini-2.5-flash-image-preview"


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on", "debug")


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


def run_image_op(
    operation: str,
    prompt: str,
    images: Optional[List[str]] = None,
    n: Optional[int] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Main entry point for image generation/editing.
    
    Args:
        operation: "generate" or "edit"
        prompt: User text prompt
        images: List of normalized data URLs (for edit only)
        n: Number of variations (default: 4, max: 8)
        debug: Include debug information in response
    
    Returns:
        {
            "success": True,
            "operation": "generate|edit",
            "urls": [list of http(s) image URLs],
            "usage": {...},
            "finish_reason": "stop",
            "debug": {...}  # if debug=True
        }
    """
    # Validate environment
    token = os.getenv("AI_PORTAL_TOKEN")
    if not token:
        return {"error": "AI_PORTAL_TOKEN required"}
    
    endpoint = os.getenv("LLM_ENDPOINT", "https://dev-ai.dragonflygroup.fr/api/v1/chat/completions")
    
    # Validate n parameter
    n_was_defaulted = (n is None)
    try:
        num = int(n) if n is not None else DEFAULT_N
    except Exception:
        return {"error": "Parameter 'n' must be an integer"}
    
    if num < 1 or num > 8:
        return {"error": "Parameter 'n' must be between 1 and 8"}
    
    # Build messages
    if operation == "generate":
        messages = build_messages_for_generate(prompt)
    elif operation == "edit":
        if not images:
            return {"error": "images required for edit"}
        messages = build_messages_for_edit(prompt, images)
    else:
        return {"error": "Invalid operation (expected 'generate' or 'edit')"}
    
    # Compute timeouts (heavier for multi-image edit)
    is_multi_edit = operation == "edit" and isinstance(images, list) and len(images) >= 2
    timeouts = get_timeouts(is_multi_edit)
    
    headers = build_headers(token)
    payload = build_payload(messages, num, MODEL)
    
    # Try batch request first
    try:
        result = _single_call(endpoint, headers, payload, timeouts)
        urls = result.get("urls", [])
        
        # If fewer URLs than requested, top up with sequential calls
        if len(urls) < num:
            remaining = num - len(urls)
            fallback = _sequential_fallback(endpoint, headers, messages, remaining, MODEL, timeouts)
            
            # Merge results
            urls.extend(fallback.get("urls", []))
            
            # Aggregate usage
            usage1 = result.get("usage") or {}
            usage2 = fallback.get("usage") or {}
            for k, v in usage2.items():
                if isinstance(v, (int, float)):
                    usage1[k] = usage1.get(k, 0) + v
            result["usage"] = usage1 or None
            result["urls"] = urls
        
        out: Dict[str, Any] = {
            "success": True,
            "operation": operation,
            "urls": result["urls"],
            "finish_reason": result.get("finish_reason"),
            "usage": result.get("usage"),
        }
        
        if debug or _env_truthy("LLM_RETURN_DEBUG"):
            out["debug"] = {
                "endpoint": endpoint,
                "model": MODEL,
                "n_requested": num,
                "n_returned": len(result["urls"]),
                "n_defaulted": n_was_defaulted,
                "messages_count": len(messages),
                "timeouts": {"connect": timeouts[0], "read": timeouts[1]},
                "raw_preview_lines": len(result.get("raw_preview", [])),
            }
        
        return out
        
    except requests.HTTPError as http_err:
        status = getattr(http_err.response, 'status_code', None)
        
        # Retry with sequential fallback for transient errors
        if status in (400, 406, 415, 502, 503, 504):
            try:
                fallback = _sequential_fallback(endpoint, headers, messages, num, MODEL, timeouts)
                
                out2: Dict[str, Any] = {
                    "success": True,
                    "operation": operation,
                    "urls": fallback["urls"],
                    "usage": fallback["usage"],
                    "finish_reason": fallback["finish_reason"],
                }
                
                if debug or _env_truthy("LLM_RETURN_DEBUG"):
                    out2["debug"] = {
                        "endpoint": endpoint,
                        "model": MODEL,
                        "note": f"Sequential fallback due to HTTP {status}",
                        "n_requested": num,
                        "n_returned": len(fallback["urls"]),
                        "timeouts": {"connect": timeouts[0], "read": timeouts[1]},
                    }
                
                return out2
            except Exception as e:
                return {"error": f"Sequential fallback failed: {e}"}
        
        # Non-retryable error
        return {"error": f"HTTP {status}: {http_err}"}
    
    except Exception as e:
        return {"error": f"Image operation failed: {e}"}
