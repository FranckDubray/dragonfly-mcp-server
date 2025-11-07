"""API routing for media transcription operations."""
from __future__ import annotations
from typing import Dict, Any
import logging

from .core import handle_get_info, handle_transcribe

logger = logging.getLogger(__name__)


def route_operation(operation: str, **params) -> Dict[str, Any]:
    """Route operation to appropriate handler with global error handling."""
    try:
        if operation == "get_info":
            return handle_get_info(path=params.get("path"))
        elif operation == "transcribe":
            return handle_transcribe(
                path=params.get("path"),
                time_start=params.get("time_start", 0),
                time_end=params.get("time_end"),
                chunk_duration=params.get("chunk_duration", 60),
                include_segments=params.get("include_segments", False),
                segment_limit=params.get("segment_limit", 100),
                model=params.get("model")
            )
        else:
            return {"error": f"Unknown operation: {operation}"}
    except Exception as e:
        logger.exception("Unhandled error in media_transcribe.api")
        return {"error": f"Unhandled error: {str(e)}"}
