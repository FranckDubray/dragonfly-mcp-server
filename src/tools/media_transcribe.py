"""Media Transcription - Extract audio from audio/video and transcribe using Whisper API.

Supports time-based segmentation and parallel processing. Returns transcript as JSON.

Example:
    {
        "tool": "media_transcribe",
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
from ._media_transcribe.api import route_operation
from ._media_transcribe import spec as _spec


def run(operation: str = None, **params) -> Dict[str, Any]:
    """Execute media transcription operation."""
    op = (operation or params.get("operation") or "transcribe").strip().lower()
    if not params.get("path"):
        return {"error": "Parameter 'path' is required"}
    return route_operation(op, **params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec."""
    return _spec()
