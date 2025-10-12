"""
SSE aggregation for image generation/editing responses.
Collects text deltas and HTTP(S) image URLs only (base64 data URLs are stripped).
"""
from typing import Any, Dict, List
import json
import re

PREVIEW_MAX = 10
# FIXED: Single slash in data:image/ (was double slash //)
DATA_URL_RE = re.compile(r"data:image/(?:png|jpeg|jpg|webp);base64,[A-Za-z0-9+\/=]+")
B64_JSON_FIELD_RE = re.compile(r'"(b64_json|image_base64)"\s*:\s*"[A-Za-z0-9+\/=]+"')
_HTTP_IMG_RE = re.compile(r"https?://[^\s\"'<>]+\.(?:png|jpe?g|webp)(?:\?[^\s\"'<>]*)?", re.IGNORECASE)


def _extract_data_str(line: str) -> str | None:
    if not line.startswith('data:'):
        return None
    return line[5:].lstrip()


def _trim_str(s: str, limit: int = 2000) -> str:
    try:
        if isinstance(s, str) and len(s) > limit:
            return s[:limit] + f"... (+{len(s)-limit} bytes)"
    except Exception:
        pass
    return s


def _sanitize_preview(s: str) -> str:
    """Remove/obfuscate base64 payloads from preview lines to avoid huge responses."""
    try:
        # Remove inline data URLs entirely
        s = DATA_URL_RE.sub("[base64_omitted]", s)
        # Replace common base64 JSON fields
        s = B64_JSON_FIELD_RE.sub(r'"\1":"[base64_omitted]"', s)
    except Exception:
        pass
    return s


def _collect_http_image_items(content_list: List[Any], http_urls: List[str]):
    for it in content_list or []:
        if isinstance(it, dict) and it.get("type") == "image_url":
            u = ((it.get("image_url") or {}).get("url"))
            if isinstance(u, str) and u.startswith("http"):
                if u not in http_urls:
                    http_urls.append(u)


def process_stream_for_images(response) -> Dict[str, Any]:
    """
    Parse SSE stream and extract:
    - Text content
    - HTTP(S) image URLs (data URLs are stripped)
    - Usage metadata
    - Preview (sanitized, limited)
    """
    content_text = ""
    finish_reason = None
    usage = None

    raw_preview: List[str] = []
    http_urls: List[str] = []

    for line_b in response.iter_lines():
        if not line_b:
            continue
        line = line_b.decode('utf-8').strip()
        data_str = _extract_data_str(line)
        if data_str is None:
            continue
        if data_str == '[DONE]':
            break
        if len(raw_preview) < PREVIEW_MAX:
            raw_preview.append(_trim_str(_sanitize_preview(data_str), 4000))
        try:
            chunk = json.loads(data_str)
            if "response" in chunk and "choices" not in chunk:
                chunk = chunk["response"]
            # usage if present
            if chunk.get("usage"):
                usage = chunk["usage"]
            choices = chunk.get("choices", [])
            for ch in choices:
                delta = ch.get("delta") or {}
                # delta.content may be text or list of items
                if isinstance(delta.get("content"), str):
                    text_piece = delta.get("content")
                    content_text += text_piece
                elif isinstance(delta.get("content"), list):
                    _collect_http_image_items(delta.get("content"), http_urls)
                # final message content (common in last chunk)
                msg = ch.get("message") or {}
                msg_content = msg.get("content")
                if isinstance(msg_content, list):
                    _collect_http_image_items(msg_content, http_urls)
                elif isinstance(msg_content, str):
                    pass
                if ch.get("finish_reason"):
                    finish_reason = ch.get("finish_reason")
        except Exception:
            continue

    # Extract http(s) image URLs from text as well
    if isinstance(content_text, str) and content_text:
        for u in _HTTP_IMG_RE.findall(content_text):
            if u not in http_urls:
                http_urls.append(u)

    return {
        "text": content_text,
        "finish_reason": finish_reason or "stop",
        "usage": usage,
        "raw_preview": raw_preview,
        "http_urls": http_urls,
    }
