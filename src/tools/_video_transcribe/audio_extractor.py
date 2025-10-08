"""Audio extraction from video using FFmpeg."""
from __future__ import annotations
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any


def extract_audio_segment(
    video_path: Path,
    start_sec: float,
    duration_sec: float,
    output_path: Path = None
) -> Dict[str, Any]:
    """
    Extract audio segment from video using FFmpeg.
    
    Args:
        video_path: Path to source video
        start_sec: Start time in seconds
        duration_sec: Duration to extract in seconds
        output_path: Output path (if None, creates temp file)
        
    Returns:
        Dict with success, audio_path, or error
    """
    try:
        # Create temp file if no output path provided
        if output_path is None:
            fd, temp_path = tempfile.mkstemp(suffix='.mp3', prefix='audio_chunk_')
            os.close(fd)
            output_path = Path(temp_path)
        
        # FFmpeg command to extract audio segment
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-ss', str(start_sec),  # Start time
            '-i', str(video_path),  # Input video
            '-t', str(duration_sec),  # Duration
            '-vn',  # No video
            '-acodec', 'libmp3lame',  # MP3 codec
            '-q:a', '2',  # Quality (0-9, 2 = high)
            '-ar', '16000',  # Sample rate 16kHz (optimal for speech)
            '-ac', '1',  # Mono channel
            str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max per segment
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"FFmpeg extraction failed: {result.stderr}"
            }
        
        # Check output file exists and has size
        if not output_path.exists():
            return {
                "success": False,
                "error": "FFmpeg did not produce output file"
            }
        
        file_size = output_path.stat().st_size
        if file_size == 0:
            return {
                "success": False,
                "error": "FFmpeg produced empty file (no audio in segment?)"
            }
        
        return {
            "success": True,
            "audio_path": str(output_path),
            "file_size": file_size,
            "duration": duration_sec
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "FFmpeg timeout (>5 minutes for segment extraction)"
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "FFmpeg not found (install FFmpeg)"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Audio extraction error: {str(e)}"
        }
