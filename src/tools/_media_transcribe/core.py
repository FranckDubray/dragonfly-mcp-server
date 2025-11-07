"""Core transcription logic for media (audio/video)."""
from __future__ import annotations
import math
import time
import logging
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .validators import validate_media_path, validate_time_range, validate_chunk_duration
from .utils import abs_from_project, probe_media_info, format_time
from .chunk_processor import process_chunk

logger = logging.getLogger(__name__)


def handle_get_info(path: str) -> Dict[str, Any]:
    """Get media information (duration, audio codec, etc.)."""
    # Validate path
    v = validate_media_path(path)
    if not v["valid"]:
        return {"error": v["error"]}

    media_path = v.get("abs_path") or abs_from_project(v["path"])
    if not media_path.exists():
        return {"error": f"File not found: {path}"}

    # Probe
    info = probe_media_info(media_path)
    if not info.get("success"):
        return {"error": info.get("error", "Unknown probe error")}

    logger.info(f"Media info retrieved: {path} ({format_time(info['duration'])})")

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
    chunk_duration: int = 60,
    include_segments: bool = False,
    segment_limit: int = 100,
    model: str | None = None
) -> Dict[str, Any]:
    """Transcribe media by extracting audio chunks and calling Whisper in parallel."""
    # Timing
    t0 = time.time()
    started_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t0))

    # 1) Validate path
    v = validate_media_path(path)
    if not v["valid"]:
        return {"error": v["error"]}

    # 2) Resolve
    media_path = v.get("abs_path") or abs_from_project(v["path"])
    if not media_path.exists():
        return {"error": f"File not found: {path}"}

    # 3) Probe
    info = probe_media_info(media_path)
    if not info.get("success"):
        return {"error": info.get("error", "Unknown probe error")}

    duration = info["duration"]
    if not info["has_audio"]:
        return {"error": "Input has no audio stream"}

    # 4) Time range
    if time_end is None:
        time_end = int(math.ceil(duration))

    tv = validate_time_range(time_start, time_end, duration)
    if not tv["valid"]:
        return {"error": tv["error"]}

    # 5) Chunk duration
    cv = validate_chunk_duration(chunk_duration)
    if not cv["valid"]:
        return {"error": cv["error"]}

    # 6) Build chunks
    actual_end = min(time_end, duration)
    dur_to_process = actual_end - time_start
    if dur_to_process <= 0:
        return {"error": "No duration to process (time_start >= time_end)"}

    chunks = []
    cur = time_start
    idx = 0
    while cur < actual_end:
        ce = min(cur + chunk_duration, actual_end)
        chunks.append({"index": idx, "start": cur, "end": ce})
        cur = ce
        idx += 1

    logger.info(f"Transcribing: {path} ({format_time(time_start)} → {format_time(actual_end)}, chunk: {chunk_duration}s, {len(chunks)} chunks, parallel=3)")

    # 7) Parallel processing
    max_workers = 3
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        fut_map = {
            executor.submit(process_chunk, media_path, c["start"], c["end"], c["index"], model): c for c in chunks
        }
        for fut in as_completed(fut_map):
            r = fut.result()
            if "error" in r:
                for f in fut_map:
                    f.cancel()
                logger.error(f"Chunk processing failed: {r['error']}")
                return {"error": r["error"]}
            results.append(r)

    # 8) Sort and assemble
    results.sort(key=lambda x: x["index"]) 

    segments_all = []
    empty_chunks = 0
    for r in results:
        if r.get("empty", False):
            empty_chunks += 1
        else:
            segments_all.append({
                "start": r["start"],
                "end": r["end"],
                "text": r["text"]
            })

    full_text = " ".join(s["text"] for s in segments_all)

    # 9) Timing and warnings
    t1 = time.time()
    completed_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t1))
    proc_time = t1 - t0

    warning = None
    if len(full_text) > 50000:
        logger.warning(f"Large transcription: {len(full_text)} chars (may exceed LLM context)")
        warning = f"⚠️ Large transcription ({len(full_text)} chars) - consider splitting ranges"

    # 10) Optional segments
    if include_segments:
        total_count = len(segments_all)
        segments_returned = segments_all[:segment_limit]
        truncated = total_count > len(segments_returned)
    else:
        segments_returned = None
        truncated = False
        total_count = len(segments_all)

    # 11) Build result
    result: Dict[str, Any] = {
        "success": True,
        "media_path": path,
        "time_start": time_start,
        "time_end": actual_end,
        "duration_processed": dur_to_process,
        "full_text": full_text,
        "metadata": {
            "total_segments": len(segments_all),
            "empty_segments": empty_chunks,
            "media_duration_total": duration,
            "audio_codec": info["audio_codec"],
            "chunk_duration": chunk_duration,
            "parallel_processing": True,
            "max_workers": max_workers,
            "text_length": len(full_text)
        },
        "timing": {
            "processing_time_seconds": round(proc_time, 2),
            "processing_time_formatted": format_time(proc_time),
            "started_at": started_at,
            "completed_at": completed_at,
            "average_time_per_second": round(proc_time / dur_to_process, 2) if dur_to_process > 0 else 0
        }
    }

    if include_segments:
        result["segments"] = segments_returned
        result["returned_count"] = len(segments_returned)
        result["total_count"] = total_count
        if truncated:
            result["truncated"] = True
            result["message"] = f"Segments truncated to first {segment_limit} items"

    if warning:
        result["warning"] = warning

    return result
