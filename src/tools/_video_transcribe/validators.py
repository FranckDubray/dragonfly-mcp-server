"""Input validation for video transcription."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any


def validate_video_path(path: str) -> Dict[str, Any]:
    """Validate video path (must be under docs/video/)."""
    if not path or not isinstance(path, str):
        return {"valid": False, "error": "path must be a non-empty string"}
    
    # Security: must be under docs/video/
    normalized = Path(path).as_posix()
    if not normalized.startswith("docs/video/"):
        return {"valid": False, "error": "Video path must be under docs/video/ (chroot security)"}
    
    return {"valid": True, "path": normalized}


def validate_time_range(time_start: int, time_end: int, duration: float) -> Dict[str, Any]:
    """Validate time_start and time_end parameters."""
    if time_start < 0:
        return {"valid": False, "error": "time_start must be >= 0"}
    
    if time_end is not None and time_end <= time_start:
        return {"valid": False, "error": "time_end must be > time_start"}
    
    if time_start >= duration:
        return {"valid": False, "error": f"time_start ({time_start}s) exceeds video duration ({duration:.1f}s)"}
    
    return {"valid": True}


def validate_chunk_duration(chunk_duration: int) -> Dict[str, Any]:
    """Validate chunk_duration parameter."""
    if chunk_duration < 10:
        return {"valid": False, "error": "chunk_duration must be >= 10 seconds"}
    
    if chunk_duration > 600:
        return {"valid": False, "error": "chunk_duration must be <= 600 seconds (10 minutes)"}
    
    return {"valid": True}
