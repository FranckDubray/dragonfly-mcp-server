"""Utility functions for media transcription."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path
from typing import Dict, Any
from uuid import uuid4


def get_project_root() -> Path:
    """Get project root directory."""
    cur = Path(__file__).resolve()
    while cur != cur.parent:
        if (cur / 'pyproject.toml').exists() or (cur / '.git').exists():
            return cur
        cur = cur.parent
    return Path.cwd()


def abs_from_project(rel_path: str) -> Path:
    """Convert relative path to absolute from project root."""
    return get_project_root() / rel_path


def ensure_media_tmp_dir() -> Path:
    """Ensure a temp directory under project chroot (docs/audio/tmp)."""
    root = get_project_root()
    tmp_dir = root / 'docs' / 'audio' / 'tmp'
    tmp_dir.mkdir(parents=True, exist_ok=True)
    return tmp_dir


def make_tmp_chunk_path(suffix: str = '.mp3') -> Path:
    """Create a unique temp chunk path under the media tmp dir (no file created)."""
    uid = uuid4().hex
    return ensure_media_tmp_dir() / f"media_chunk_{uid}{suffix}"


def format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def probe_media_info(path: Path) -> Dict[str, Any]:
    """Get media metadata using ffprobe (duration, audio codec, has_audio)."""
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration:stream=codec_type,codec_name',
            '-of', 'json',
            str(path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return {"error": f"ffprobe failed: {result.stderr}"}
        data = json.loads(result.stdout)
        duration = float(data.get('format', {}).get('duration', 0))
        audio_codec = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'audio':
                audio_codec = stream.get('codec_name')
                break
        return {
            "success": True,
            "duration": duration,
            "audio_codec": audio_codec,
            "has_audio": audio_codec is not None
        }
    except subprocess.TimeoutExpired:
        return {"error": "ffprobe timeout (>30s)"}
    except FileNotFoundError:
        return {"error": "ffprobe not found (install FFmpeg)"}
    except Exception as e:
        return {"error": f"ffprobe error: {str(e)}"}
