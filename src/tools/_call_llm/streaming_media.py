from __future__ import annotations
"""
Multimodal media extraction helpers (images/files from LLM responses)
"""
from typing import Any, Dict, List


def collect_media_from_gemini_content(content: Any) -> List[Dict[str, Any]]:
    """Extract media (images/files) from Gemini-style content.parts structure"""
    media: List[Dict[str, Any]] = []
    try:
        parts = None
        if isinstance(content, dict) and isinstance(content.get("parts"), list):
            parts = content["parts"]
        elif isinstance(content, list):
            parts = content
        if not parts:
            return media
        for part in parts:
            if not isinstance(part, dict):
                continue
            mime = part.get("mime_type") or part.get("mimeType")
            # inline_data (base64)
            inline = part.get("inline_data") or part.get("inlineData")
            if isinstance(inline, dict) and inline.get("data"):
                media.append({
                    "kind": "inline",
                    "mime_type": mime,
                    "data_base64": inline.get("data")[:100000] if isinstance(inline.get("data"), str) else inline.get("data"),
                })
                continue
            # fileUri / file_uri
            file_uri = part.get("fileUri") or part.get("file_uri")
            if isinstance(file_uri, str):
                media.append({
                    "kind": "url",
                    "mime_type": mime,
                    "url": file_uri,
                })
                continue
            # file_data may contain {fileUri: ...}
            file_data = part.get("file_data") or part.get("fileData")
            if isinstance(file_data, dict):
                fu = file_data.get("fileUri") or file_data.get("file_uri")
                if isinstance(fu, str):
                    media.append({
                        "kind": "url",
                        "mime_type": mime or file_data.get("mime_type") or file_data.get("mimeType"),
                        "url": fu,
                    })
                    continue
            # generic url / image_url
            image_url = part.get("image_url")
            if isinstance(image_url, str):
                media.append({"kind": "url", "mime_type": mime, "url": image_url})
                continue
            if isinstance(image_url, dict) and isinstance(image_url.get("url"), str):
                media.append({"kind": "url", "mime_type": mime, "url": image_url["url"]})
                continue
            if isinstance(part.get("url"), str):
                media.append({"kind": "url", "mime_type": mime, "url": part.get("url")})
                continue
    except Exception:
        pass
    return media


def collect_media_from_openai_message_content(content: Any) -> List[Dict[str, Any]]:
    """Extract media from OpenAI-style message.content array"""
    media: List[Dict[str, Any]] = []
    try:
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                typ = (item.get("type") or "").lower()
                # image_url can be string or object {url: ...}
                if "image_url" in item:
                    v = item.get("image_url")
                    if isinstance(v, str):
                        media.append({"kind": "url", "url": v})
                    elif isinstance(v, dict) and isinstance(v.get("url"), str):
                        media.append({"kind": "url", "url": v["url"]})
                # generic url
                elif isinstance(item.get("url"), str) and typ in ("image", "image_url", "file", "media"):
                    media.append({"kind": "url", "url": item["url"]})
    except Exception:
        pass
    return media
