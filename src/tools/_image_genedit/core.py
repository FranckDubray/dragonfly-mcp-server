from typing import Any, Dict, List, Optional, Tuple
import os
import base64

import requests

from .client import build_headers, post_stream, post_json
from .streaming import process_stream_for_images
from .payloads import (
    DEFAULT_FORMAT, DEFAULT_N, DEFAULT_RATIO, DEFAULT_SIZE,
    infer_dimensions, build_messages_for_generate, build_messages_for_edit, build_initial_payload,
)
from .dims import infer_from_sources
from .utils import extract_image_urls, download_to_data_url


MODEL = "gemini-2.5-flash-image-preview"
MIN_SIZE = 64
MAX_SIZE = 4096


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on", "debug")


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, int(v)))


def _get_int_env(name: str, default: int) -> int:
    try:
        v = os.getenv(name, "").strip()
        if v == "":
            return default
        return int(v)
    except Exception:
        return default


def _single_call(endpoint: str, headers: Dict[str, str], payload: Dict[str, Any], timeout_sec: int, timeouts_override: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
    # Some backends reject stream for image tasks; try non-stream JSON first, then fallback to stream
    try:
        resp = post_json(endpoint, headers, payload, timeout_sec, timeouts_override=timeouts_override)
        # If non-stream returns JSON with images directly
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
                            if isinstance(u, str):
                                if u.startswith("http"):
                                    http_urls.append(u)
            # 2) Provider sometimes gives an <img src="https://..."></img> tag (in delta content)
            if not http_urls:
                text = "".join([(c.get("delta", {}).get("content") or "") for c in (j.get("choices") or [])])
                if isinstance(text, str) and text:
                    for u in extract_image_urls(text):
                        http_urls.append(u)
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
        # Fallback to stream parsing
    except Exception:
        pass
    # Ensure payload requests streaming in fallback
    payload_stream = dict(payload)
    payload_stream["stream"] = True
    resp = post_stream(endpoint, headers, payload_stream, timeout_sec, timeouts_override=timeouts_override)
    res = process_stream_for_images(resp)
    # Extract possible http(s) image URLs from text content and from SSE items (ignore base64 data URLs)
    http_urls: List[str] = []
    # From SSE collected items
    for u in (res.get("http_urls") or []):
        if isinstance(u, str) and u.startswith("http"):
            http_urls.append(u)
    # From text content
    if isinstance(res.get("text"), str) and res["text"]:
        for u in extract_image_urls(res["text"]):
            http_urls.append(u)
    # Dedupe preserving order
    seen = set()
    http_urls = [u for u in http_urls if not (u in seen or seen.add(u))]
    return {
        "urls": http_urls,
        "finish_reason": res.get("finish_reason"),
        "usage": res.get("usage"),
        "raw_preview": res.get("raw_preview"),
    }


def run_image_op(
    operation: str,
    prompt: str,
    images: Optional[List[str]] = None,
    format: Optional[str] = None,
    ratio: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    n: Optional[int] = None,
    debug: bool = False,
    image_urls: Optional[List[str]] = None,
) -> Dict[str, Any]:
    # Validate env
    token = os.getenv("AI_PORTAL_TOKEN")
    if not token:
        return {"error": "AI_PORTAL_TOKEN required"}
    endpoint = os.getenv("LLM_ENDPOINT", "https://dev-ai.dragonflygroup.fr/api/v1/chat/completions")
    timeout_sec = int(os.getenv("LLM_REQUEST_TIMEOUT_SEC", "180"))

    # Defaults
    fmt = (format or DEFAULT_FORMAT).lower()
    if fmt == "jpeg":
        fmt = "jpg"
    if fmt not in ("png", "jpg"):
        return {"error": "Unsupported format (expected 'png' or 'jpg')"}

    # n variations (must be >=1)
    n_was_defaulted = False
    try:
        if n is None:
            n_was_defaulted = True
        num = int(n) if n is not None else DEFAULT_N
    except Exception:
        return {"error": "Parameter 'n' must be an integer"}
    if num < 1:
        return {"error": "Parameter 'n' must be >= 1"}

    # Always inline inputs for edit: http(s)->data URL, base64->data URL (robust like image_orchestrator)
    if operation == "edit":
        srcs: Optional[List[str]] = images if (images and isinstance(images, list) and len(images) > 0) else None
        if not srcs and isinstance(image_urls, list) and len(image_urls) > 0:
            srcs = image_urls
        if not srcs:
            return {"error": "images (list) is required for edit (accepts http(s), data:URL, or base64)"}
        if len(srcs) < 1 or len(srcs) > 3:
            return {"error": "images must contain 1 to 3 items"}
        normalized: List[str] = []
        for im in srcs:
            if not isinstance(im, str):
                continue
            s = im.strip()
            if not s:
                continue
            if s.startswith("data:"):
                normalized.append(s)
                continue
            if s.startswith("http://") or s.startswith("https://"):
                du = download_to_data_url(s)
                if du:
                    normalized.append(du)
                else:
                    # fallback: keep http(s) if download fails
                    normalized.append(s)
                continue
            # Try raw base64
            try:
                base64.b64decode(s, validate=True)
                normalized.append(f"data:image/png;base64,{s}")
            except Exception:
                # if not valid base64, keep as-is (best effort)
                normalized.append(s)
        if not normalized:
            return {"error": "Could not prepare images (must be http(s), data:URL, or valid base64)"}
        images = normalized

    # Dimensions: inherit for edit if possible (when no explicit dims)
    if operation == "edit" and images:
        if not width and not height:
            # Only possible when images are data URLs; for http(s) we skip inference
            if all(isinstance(u, str) and u.startswith("data:") for u in images):
                src_w, src_h = infer_from_sources(images)
                if src_w and src_h:
                    width, height = src_w, src_h

    # Compute final dims
    r = ratio or DEFAULT_RATIO
    w, h = infer_dimensions(r, width, height)

    # Clamp to safe bounds (64..4096)
    w_clamped = _clamp(w, MIN_SIZE, MAX_SIZE)
    h_clamped = _clamp(h, MIN_SIZE, MAX_SIZE)

    # Build messages
    if operation == "generate":
        messages = build_messages_for_generate(prompt)
    elif operation == "edit":
        if not images:
            return {"error": "images required for edit"}
        messages = build_messages_for_edit(prompt, images)
    else:
        return {"error": "Invalid operation"}

    headers = build_headers(token)

    # Compute per-call timeouts override: heavier for edit with >= 2 images
    timeouts_override: Optional[Tuple[int, int]] = None
    if operation == "edit":
        try:
            count_sources = len(images or [])
        except Exception:
            count_sources = 0
        if count_sources >= 2:
            connect_to = _get_int_env("IMAGE_MULTI_CONNECT_TIMEOUT_SEC", 30)
            read_to = _get_int_env("IMAGE_MULTI_REQUEST_TIMEOUT_SEC", 900)
            timeouts_override = (connect_to, read_to)

    # First attempt: single request with n. If backend rejects (406), fallback to sequential without n and without stream
    payload = build_initial_payload(messages, num, MODEL, w_clamped, h_clamped, fmt)

    try:
        # Explicit non-stream on first attempt
        payload_non_stream = dict(payload)
        payload_non_stream["stream"] = False
        result = _single_call(endpoint, headers, payload_non_stream, timeout_sec, timeouts_override=timeouts_override)
        first_urls = result.get("urls", [])
        out: Dict[str, Any] = {
            "success": True,
            "operation": operation,
            "urls": list(first_urls),
            "finish_reason": result.get("finish_reason"),
            "usage": result.get("usage"),
        }
        if debug or _env_truthy("LLM_RETURN_DEBUG"):
            out["debug"] = {
                "endpoint": endpoint,
                "model": MODEL,
                "payload_summary": {
                    "n": num,
                    "n_defaulted": bool(n_was_defaulted),
                    "messages_count": len(messages),
                    "stream": True,
                    "dims": {"fixed_output": {"width": DEFAULT_SIZE, "height": DEFAULT_SIZE, "ratio": DEFAULT_RATIO}},
                },
                "raw_preview": result.get("raw_preview"),
                "urls": first_urls,
            }
        # If fewer URLs than requested, top-up with sequential 1-by-1 calls
        current_count = len(out["urls"]) if out.get("urls") else 0
        if current_count < num:
            remaining = num - current_count
            usages: List[Dict[str, Any]] = []
            http_urls_agg: List[str] = list(out.get("urls") or [])
            urls_fallback: List[str] = []
            for _ in range(remaining):
                payload1 = build_initial_payload(messages, 1, MODEL, w_clamped, h_clamped, fmt)
                payload1.pop("n", None)
                res1 = _single_call(endpoint, headers, payload1, timeout_sec, timeouts_override=timeouts_override)
                if res1.get("usage"):
                    usages.append(res1["usage"]) 
                urls_new = res1.get("urls", []) or []
                http_urls_agg.extend(urls_new)
                urls_fallback.extend(urls_new)
            # aggregate usage
            usage_agg: Dict[str, Any] = out.get("usage") or {}
            for u in usages:
                for k, v in u.items():
                    if isinstance(v, (int, float)):
                        usage_agg[k] = usage_agg.get(k, 0) + v
            out.update({"usage": usage_agg or out.get("usage"), "urls": http_urls_agg})
            if debug or _env_truthy("LLM_RETURN_DEBUG"):
                out["debug"]["urls_fallback"] = urls_fallback
        return out
    except requests.HTTPError as http_err:
        status = getattr(http_err.response, 'status_code', None)
        # Include transient 5xx for fallback path
        if status in (400, 404, 406, 415, 502, 503, 504):
            usages: List[Dict[str, Any]] = []
            http_urls_agg: List[str] = []
            for _ in range(num):
                payload1 = build_initial_payload(messages, 1, MODEL, w_clamped, h_clamped, fmt)
                payload1.pop("n", None)
                res1 = _single_call(endpoint, headers, payload1, timeout_sec, timeouts_override=timeouts_override)
                if res1.get("usage"):
                    usages.append(res1["usage"]) 
                http_urls_agg.extend(res1.get("urls", []) or [])
            usage_agg: Dict[str, Any] = {}
            for u in usages:
                for k, v in u.items():
                    if isinstance(v, (int, float)):
                        usage_agg[k] = usage_agg.get(k, 0) + v
            out2: Dict[str, Any] = {
                "success": True,
                "operation": operation,
                "urls": http_urls_agg,
                "usage": usage_agg or None,
                "finish_reason": "stop",
            }
            if debug or _env_truthy("LLM_RETURN_DEBUG"):
                out2["debug"] = {
                    "endpoint": endpoint,
                    "model": MODEL,
                    "note": "Fallback sequential calls due to backend rejection/timeout (400/404/406/415/5xx)",
                    "payload_summary": {
                        "n": num,
                        "n_defaulted": bool(n_was_defaulted),
                        "messages_count": len(messages),
                        "stream": True,
                        "dims": {"fixed_output": {"width": DEFAULT_SIZE, "height": DEFAULT_SIZE, "ratio": DEFAULT_RATIO}},
                    },
                    "urls_fallback": http_urls_agg,
                }
            return out2
        raise
    except Exception as e:
        # Last-chance fallback: try 1-by-1 once
        try:
            usages: List[Dict[str, Any]] = []
            http_urls_agg: List[str] = []
            for _ in range(num or 1):
                payload1 = build_initial_payload(messages, 1, MODEL, w_clamped, h_clamped, fmt)
                payload1.pop("n", None)
                res1 = _single_call(endpoint, headers, payload1, timeout_sec, timeouts_override=timeouts_override)
                if res1.get("usage"):
                    usages.append(res1["usage"]) 
                http_urls_agg.extend(res1.get("urls", []) or [])
            usage_agg: Dict[str, Any] = {}
            for u in usages:
                for k, v in u.items():
                    if isinstance(v, (int, float)):
                        usage_agg[k] = usage_agg.get(k, 0) + v
            out3: Dict[str, Any] = {
                "success": True,
                "operation": operation,
                "urls": http_urls_agg,
                "usage": usage_agg or None,
                "finish_reason": "stop",
            }
            if debug or _env_truthy("LLM_RETURN_DEBUG"):
                out3["debug"] = {
                    "endpoint": endpoint,
                    "model": MODEL,
                    "note": f"Last-chance fallback after exception: {e}",
                    "payload_summary": {
                        "n": num,
                        "n_defaulted": bool(n_was_defaulted),
                        "messages_count": len(messages),
                        "stream": True,
                        "dims": {"fixed_output": {"width": DEFAULT_SIZE, "height": DEFAULT_SIZE, "ratio": DEFAULT_RATIO}},
                    },
                    "urls_fallback": http_urls_agg,
                }
            return out3
        except Exception:
            return {"error": f"generate_edit_image failed: {e}"}
