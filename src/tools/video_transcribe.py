"""Video Transcription - Extract audio from video and transcribe using Whisper API.

Supports time-based segmentation for large videos. Returns transcript as JSON.

Example:
    {
        "tool": "video_transcribe",
        "params": {
            "operation": "transcribe",
            "path": "docs/video/conference.mp4",
            "time_start": 0,
            "time_end": 3600,
            "chunk_duration": 60
        }
    }
"""
from __future__ import annotations
from typing import Dict, Any

# Import from package implementation (with _)
from ._video_transcribe.api import route_operation
from ._video_transcribe import spec as _spec


def run(operation: str = None, **params) -> Dict[str, Any]:
    """Execute video transcription operation.
    
    Args:
        operation: Operation to perform (transcribe, get_info)
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    # Normalize operation
    op = (operation or params.get("operation") or "transcribe").strip().lower()
    
    # Validate required params
    if not params.get("path"):
        return {"error": "Parameter 'path' is required"}
    
    # Route to handler
    return route_operation(op, **params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    return _spec()
