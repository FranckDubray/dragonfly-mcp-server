"""Core transcription logic."""
from __future__ import annotations
import math
import time
import logging
from pathlib import Path
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .validators import validate_video_path, validate_time_range, validate_chunk_duration
from .utils import abs_from_project, probe_video_info, format_time
from .chunk_processor import process_chunk

logger = logging.getLogger(__name__)


def handle_get_info(path: str) -> Dict[str, Any]:
    """Get video information (duration, audio codec, etc.)."""
    # Validate path
    path_validation = validate_video_path(path)
    if not path_validation["valid"]:
        return {"error": path_validation["error"]}
    
    # Get absolute path
    video_path = abs_from_project(path_validation["path"])
    if not video_path.exists():
        return {"error": f"Video file not found: {path}"}
    
    # Probe video
    info = probe_video_info(video_path)
    if not info.get("success"):
        return {"error": info.get("error", "Unknown probe error")}
    
    logger.info(f"Video info retrieved: {path} ({format_time(info['duration'])})")
    
    return {
        "success": True,
        "path": path,
        "duration": info["duration"],
        "duration_formatted": format_time(info["duration"]),
        "audio_codec": info["audio_codec"],
        "has_audio": info["has_audio"]
    }


def handle_transcribe(
    path: str,
    time_start: int = 0,
    time_end: int = None,
    chunk_duration: int = 60
) -> Dict[str, Any]:
    """
    Transcribe video audio using Whisper API (parallel processing by batch of 3).
    
    Args:
        path: Video path (relative to project, under docs/video/)
        time_start: Start time in seconds (default: 0)
        time_end: End time in seconds (default: video duration)
        chunk_duration: Internal chunk size in seconds (default: 60)
        
    Returns:
        Dict with success, full_text, metadata (segments excluded to reduce payload)
    """
    # Start timing
    start_time = time.time()
    start_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))
    
    # 1. Validate path
    path_validation = validate_video_path(path)
    if not path_validation["valid"]:
        return {"error": path_validation["error"]}
    
    # 2. Get video info
    video_path = abs_from_project(path_validation["path"])
    if not video_path.exists():
        return {"error": f"Video file not found: {path}"}
    
    info = probe_video_info(video_path)
    if not info.get("success"):
        return {"error": info.get("error", "Unknown probe error")}
    
    duration = info["duration"]
    
    if not info["has_audio"]:
        return {"error": "Video has no audio stream"}
    
    # 3. Validate time range
    if time_end is None:
        time_end = int(math.ceil(duration))
    
    time_validation = validate_time_range(time_start, time_end, duration)
    if not time_validation["valid"]:
        return {"error": time_validation["error"]}
    
    # 4. Validate chunk duration
    chunk_validation = validate_chunk_duration(chunk_duration)
    if not chunk_validation["valid"]:
        return {"error": chunk_validation["error"]}
    
    # 5. Calculate chunks
    actual_end = min(time_end, duration)
    duration_to_process = actual_end - time_start
    
    if duration_to_process <= 0:
        return {"error": "No duration to process (time_start >= time_end)"}
    
    logger.info(f"Transcribing: {path} ({format_time(time_start)} → {format_time(actual_end)}, chunk: {chunk_duration}s)")
    
    # 6. Build chunk list
    chunks = []
    current = time_start
    chunk_index = 0
    
    while current < actual_end:
        chunk_end = min(current + chunk_duration, actual_end)
        chunks.append({
            "index": chunk_index,
            "start": current,
            "end": chunk_end
        })
        current = chunk_end
        chunk_index += 1
    
    logger.info(f"Processing {len(chunks)} chunks in parallel (max 3 workers)")
    
    # 7. Process chunks in parallel (batch of 3)
    segments = []
    max_workers = 3  # Process 3 chunks in parallel
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all chunks
        future_to_chunk = {
            executor.submit(
                process_chunk,
                video_path,
                chunk["start"],
                chunk["end"],
                chunk["index"]
            ): chunk for chunk in chunks
        }
        
        # Collect results as they complete
        results = []
        for future in as_completed(future_to_chunk):
            result = future.result()
            
            # Check for errors
            if "error" in result:
                # Cancel remaining futures
                for f in future_to_chunk:
                    f.cancel()
                logger.error(f"Chunk processing failed: {result['error']}")
                return {"error": result["error"]}
            
            results.append(result)
    
    # 8. Sort by index to preserve order
    results.sort(key=lambda x: x["index"])
    
    # 9. Build segments list (filter out empty chunks)
    segments = []
    empty_chunks = 0
    
    for r in results:
        if r.get("empty", False):
            # Skip empty chunks (silence/music)
            empty_chunks += 1
        else:
            segments.append({
                "start": r["start"],
                "end": r["end"],
                "text": r["text"]
            })
    
    # 10. Assemble full text (only non-empty segments)
    full_text = " ".join(seg["text"] for seg in segments)
    
    # 11. Calculate execution time
    end_time = time.time()
    end_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
    processing_time = end_time - start_time
    
    logger.info(f"Transcription complete: {len(full_text)} chars in {format_time(processing_time)}")
    
    # 12. Truncation warning if text is very long
    truncation_warning = None
    if len(full_text) > 50000:
        logger.warning(f"Large transcription: {len(full_text)} chars (may exceed LLM context)")
        truncation_warning = f"⚠️ Large transcription ({len(full_text)} chars) - consider splitting video"
    
    # 13. Return result (WITHOUT segments to reduce payload size)
    result = {
        "success": True,
        "video_path": path,
        "time_start": time_start,
        "time_end": actual_end,
        "duration_processed": duration_to_process,
        "full_text": full_text,
        "metadata": {
            "total_segments": len(segments),
            "empty_segments": empty_chunks,  # Number of chunks skipped (silence/music)
            "video_duration_total": duration,
            "audio_codec": info["audio_codec"],
            "chunk_duration": chunk_duration,
            "parallel_processing": True,
            "max_workers": max_workers,
            "text_length": len(full_text)
        },
        "timing": {
            "processing_time_seconds": round(processing_time, 2),
            "processing_time_formatted": format_time(processing_time),
            "started_at": start_timestamp,
            "completed_at": end_timestamp,
            "average_time_per_second": round(processing_time / duration_to_process, 2) if duration_to_process > 0 else 0
        }
    }
    
    if truncation_warning:
        result["warning"] = truncation_warning
    
    return result
