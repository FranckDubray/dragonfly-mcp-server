"""Chunk processing for media transcription (audio/video sources)."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional

from .audio_extractor import extract_audio_segment
from .whisper_client import transcribe_audio_file


def process_chunk(media_path: Path, start: float, end: float, index: int, whisper_model: Optional[str] = None) -> Dict[str, Any]:
    """Extract audio segment and transcribe with Whisper API.

    Args:
        media_path: source media path (audio or video)
        start: start time (seconds)
        end: end time (seconds)
        index: chunk index
        whisper_model: optional model hint for backend
    """
    duration = end - start

    # Extract audio as mp3 16k mono
    extract_result = extract_audio_segment(media_path, start, duration)
    if not extract_result.get("success"):
        return {
            "index": index,
            "error": f"Audio extraction failed at {start:.2f}s: {extract_result.get('error')}"
        }

    audio_path = Path(extract_result["audio_path"])

    # Transcribe
    transcribe_result = transcribe_audio_file(audio_path, whisper_model=whisper_model)

    # Cleanup temp
    try:
        audio_path.unlink()
    except Exception:
        pass

    if not transcribe_result.get("success"):
        return {
            "index": index,
            "error": f"Transcription failed at {start:.2f}s: {transcribe_result.get('error')}"
        }

    if transcribe_result.get("empty", False):
        return {
            "index": index,
            "start": start,
            "end": end,
            "text": "",
            "empty": True
        }

    return {
        "index": index,
        "start": start,
        "end": end,
        "text": transcribe_result["transcription"]
    }
