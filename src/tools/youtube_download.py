"""YouTube Download - Download videos or audio from YouTube URLs.

Supports audio-only (perfect for transcription), video, or both.
Files are saved to docs/video/ for seamless integration with video_transcribe tool.

Example usage:
    # Download audio only (best for transcription)
    {
        "tool": "youtube_download",
        "params": {
            "operation": "download",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "media_type": "audio"
        }
    }
    
    # Download video
    {
        "tool": "youtube_download",
        "params": {
            "operation": "download",
            "url": "https://youtu.be/dQw4w9WgXcQ",
            "media_type": "video",
            "quality": "720p",
            "filename": "my_video"
        }
    }
    
    # Get video info without downloading
    {
        "tool": "youtube_download",
        "params": {
            "operation": "get_info",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }
    }

Workflow for transcription:
    1. youtube_download (media_type="audio") → saves to docs/video/
    2. video_transcribe (use the path from step 1) → extracts text
"""
from __future__ import annotations
from typing import Dict, Any

# Import from implementation package
from ._youtube_download.api import route_operation
from ._youtube_download import spec as _spec


def run(operation: str = "download", **params) -> Dict[str, Any]:
    """Execute YouTube download operation.
    
    Args:
        operation: Operation to perform ("download" or "get_info")
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    # Normalize operation
    op = (operation or params.get("operation") or "download").strip().lower()
    
    # Validate required params for download
    if op == "download":
        if not params.get("url"):
            return {"error": "Parameter 'url' is required for download operation"}
    
    # Validate required params for get_info
    elif op == "get_info":
        if not params.get("url"):
            return {"error": "Parameter 'url' is required for get_info operation"}
    
    # Route to handler
    return route_operation(op, **params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    return _spec()
