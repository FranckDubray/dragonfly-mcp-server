"""
Payload construction for image generation/editing.
Backend is fixed to 1024x1024 PNG output.
"""
from typing import Any, Dict, List

DEFAULT_N = 1
DEFAULT_SIZE = 1024


def build_messages_for_generate(prompt: str) -> List[Dict[str, Any]]:
    """Build messages for image generation (text only)."""
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ]
        }
    ]


def build_messages_for_edit(prompt: str, images_data_urls: List[str]) -> List[Dict[str, Any]]:
    """Build messages for image editing (text + images)."""
    content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
    for url in images_data_urls:
        content.append({
            "type": "image_url",
            "image_url": {"url": url}
        })
    return [{"role": "user", "content": content}]


def build_payload(messages: List[Dict[str, Any]], n: int, model: str) -> Dict[str, Any]:
    """
    Build minimal API payload.
    
    NOTE: Backend is fixed to 1024x1024 PNG output.
    Width/height/format parameters are NOT sent (ignored by backend).
    """
    return {
        "model": model,
        "messages": messages,
        "temperature": 1,
        "stream": True,
        "n": n,
    }
