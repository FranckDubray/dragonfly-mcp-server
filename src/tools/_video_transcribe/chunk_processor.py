"""Chunk processing logic for parallel transcription."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

from .audio_extractor import extract_audio_segment
from .whisper_client import transcribe_audio_file
from .utils import format_time


def process_chunk(video_path: Path, start: float, end: float, index: int) -> Dict[str, Any]:
    """
    Process a single chunk (extract audio + transcribe).
    
    Args:
        video_path: Path to video
        start: Start time in seconds
        end: End time in seconds
        index: Chunk index (for ordering)
        
    Returns:
        Dict with index, start, end, text, or error (or empty flag)
    """
    chunk_dur = end - start
    
    # Extract audio segment (temp file)
    extract_result = extract_audio_segment(video_path, start, chunk_dur)
    
    if not extract_result.get("success"):
        return {
            "index": index,
            "error": f"Audio extraction failed at {format_time(start)}: {extract_result.get('error')}"
        }
    
    audio_path = Path(extract_result["audio_path"])
    
    # Transcribe with Whisper API
    transcribe_result = transcribe_audio_file(audio_path)
    
    # Cleanup temp audio file immediately
    try:
        audio_path.unlink()
    except Exception:
        pass  # Best effort cleanup
    
    if not transcribe_result.get("success"):
        return {
            "index": index,
            "error": f"Transcription failed at {format_time(start)}: {transcribe_result.get('error')}"
        }
    
    # Check if transcription is empty (silence/music)
    if transcribe_result.get("empty", False):
        return {
            "index": index,
            "start": start,
            "end": end,
            "text": "",
            "empty": True  # Flag to indicate this chunk was empty
        }
    
    # Return segment
    return {
        "index": index,
        "start": start,
        "end": end,
        "text": transcribe_result["transcription"]
    }
