"""Audio extraction from media (audio or video) using FFmpeg.

Ensures temp chunks are written under project chroot (docs/audio/tmp).
"""
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Dict, Any

from .utils import make_tmp_chunk_path


def extract_audio_segment(
    input_path: Path,
    start_sec: float,
    duration_sec: float,
    output_path: Path | None = None
) -> Dict[str, Any]:
    """Extract audio segment as MP3 mono 16kHz via FFmpeg.

    Chunks are stored under docs/audio/tmp to respect chroot constraints.
    """
    try:
        # Create chrooted temp file if no output path provided
        if output_path is None:
            output_path = make_tmp_chunk_path(suffix='.mp3')

        cmd = [
            'ffmpeg',
            '-y',
            '-ss', str(start_sec),
            '-t', str(duration_sec),
            '-i', str(input_path),
            '-vn',
            '-acodec', 'libmp3lame',
            '-q:a', '2',
            '-ar', '16000',
            '-ac', '1',
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return {"success": False, "error": f"FFmpeg extraction failed: {result.stderr}"}
        if not output_path.exists():
            return {"success": False, "error": "FFmpeg did not produce output file"}
        if output_path.stat().st_size == 0:
            return {"success": False, "error": "FFmpeg produced empty file (no audio in segment?)"}
        return {"success": True, "audio_path": str(output_path), "file_size": output_path.stat().st_size, "duration": duration_sec}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "FFmpeg timeout (>5 minutes for segment extraction)"}
    except FileNotFoundError:
        return {"success": False, "error": "FFmpeg not found (install FFmpeg)"}
    except Exception as e:
        return {"success": False, "error": f"Audio extraction error: {str(e)}"}
