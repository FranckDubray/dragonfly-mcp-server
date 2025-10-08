"""YouTube Download package - internal implementation."""
from __future__ import annotations
from typing import Dict, Any
import json
from pathlib import Path


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    spec_path = Path(__file__).parent.parent.parent / "tool_specs" / "youtube_download.json"
    
    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback minimal spec (should not happen in production)
        return {
            "type": "function",
            "function": {
                "name": "youtube_download",
                "displayName": "YouTube Downloader",
                "description": "Download videos or audio from YouTube URLs",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["download", "get_info"]},
                        "url": {"type": "string"},
                        "media_type": {"type": "string", "enum": ["audio", "video", "both"]},
                    },
                    "required": ["url"],
                    "additionalProperties": False
                }
            }
        }


# Export spec for bootstrap file
__all__ = ["spec"]
