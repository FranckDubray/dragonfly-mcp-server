"""Input validation for media transcription (audio or video)."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

from .utils import get_project_root


def validate_media_path(path: str) -> Dict[str, Any]:
    """Validate media path and enforce chroot (docs/audio or docs/video).

    Returns a dict with:
    - valid: bool
    - path: normalized relative path (echo purpose only)
    - abs_path: absolute resolved path (safe to use)
    - error: message when invalid
    """
    if not path or not isinstance(path, str):
        return {"valid": False, "error": "path must be a non-empty string"}

    normalized = Path(path).as_posix()
    root = get_project_root().resolve()
    abs_candidate = (root / normalized).resolve()

    audio_root = (root / "docs" / "audio").resolve()
    video_root = (root / "docs" / "video").resolve()

    allowed = abs_candidate.is_relative_to(audio_root) or abs_candidate.is_relative_to(video_root)
    if not allowed:
        return {
            "valid": False,
            "error": "Path must resolve under docs/audio/ or docs/video/ (chroot security)"
        }

    return {"valid": True, "path": normalized, "abs_path": abs_candidate}


def validate_time_range(time_start: int, time_end: int, duration: float) -> Dict[str, Any]:
    """Validate time_start and time_end parameters against media duration."""
    if time_start < 0:
        return {"valid": False, "error": "time_start must be >= 0"}
    if time_end is not None and time_end <= time_start:
        return {"valid": False, "error": "time_end must be > time_start"}
    if time_start >= duration:
        return {"valid": False, "error": f"time_start ({time_start}s) exceeds media duration ({duration:.1f}s)"}
    return {"valid": True}


def validate_chunk_duration(chunk_duration: int) -> Dict[str, Any]:
    """Validate chunk_duration bounds."""
    if chunk_duration < 10:
        return {"valid": False, "error": "chunk_duration must be >= 10 seconds"}
    if chunk_duration > 600:
        return {"valid": False, "error": "chunk_duration must be <= 600 seconds (10 minutes)"}
    return {"valid": True}
