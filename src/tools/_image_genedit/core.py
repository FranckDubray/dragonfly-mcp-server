"""
Core image generation/editing logic.
Main entry point with logging and minimal output.
"""
from typing import Any, Dict, List, Optional
import os
import logging
import requests

from .client import build_headers, get_timeouts
from .operations import _single_call, _sequential_fallback
from .payloads import DEFAULT_N, build_messages_for_generate, build_messages_for_edit, build_payload

logger = logging.getLogger(__name__)

MODEL = "gemini-2.5-flash-image-preview"


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on", "debug")


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
            "urls": [list of http(s) image URLs],
            "usage": {...},
            "finish_reason": "stop",
            "debug": {...}  # if debug=True
        }
    """
    # Validate environment
    token = os.getenv("AI_PORTAL_TOKEN")
    if not token:
        logger.error("AI_PORTAL_TOKEN not configured")
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
        logger.info(f"Image generation: n={num}, prompt={prompt[:50]}...")
    elif operation == "edit":
        if not images:
            return {"error": "images required for edit"}
        messages = build_messages_for_edit(prompt, images)
        logger.info(f"Image edit: n={num}, images_count={len(images)}, prompt={prompt[:50]}...")
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
            logger.warning(f"Batch returned {len(urls)}/{num} images, using sequential fallback for remaining {num - len(urls)}")
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
        
        logger.info(f"Image {operation} completed: {len(result['urls'])} URLs returned")
        
        out: Dict[str, Any] = {
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
        logger.error(f"HTTP {status} during {operation}: {http_err}")
        
        # Retry with sequential fallback for transient errors
        if status in (400, 406, 415, 502, 503, 504):
            logger.warning(f"Attempting sequential fallback due to HTTP {status}")
            try:
                fallback = _sequential_fallback(endpoint, headers, messages, num, MODEL, timeouts)
                logger.info(f"Sequential fallback completed: {len(fallback['urls'])} URLs")
                
                out2: Dict[str, Any] = {
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
                logger.error(f"Sequential fallback failed: {e}")
                return {"error": f"Sequential fallback failed: {e}"}
        
        # Non-retryable error
        return {"error": f"HTTP {status}: {http_err}"}
    
    except Exception as e:
        logger.error(f"Image operation failed: {e}")
        return {"error": f"Image operation failed: {e}"}
