"""Input validation for YouTube download operations."""
from __future__ import annotations
from typing import Dict, Any
from urllib.parse import urlparse, parse_qs
import re


YOUTUBE_DOMAINS = [
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "www.youtu.be",
]


def validate_youtube_url(url: str) -> Dict[str, Any]:
    """Validate YouTube URL format.
    
    Args:
        url: YouTube video URL
        
    Returns:
        {"valid": bool, "error": str (if invalid), "video_id": str (if valid)}
    """
    if not url or not isinstance(url, str):
        return {"valid": False, "error": "URL must be a non-empty string"}
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        return {"valid": False, "error": f"Invalid URL format: {e}"}
    
    # Check domain
    if parsed.netloc not in YOUTUBE_DOMAINS:
        return {
            "valid": False,
            "error": f"URL must be from YouTube (got: {parsed.netloc}). Supported: {', '.join(YOUTUBE_DOMAINS)}"
        }
    
    # Extract video ID
    video_id = None
    
    # Format: youtube.com/watch?v=VIDEO_ID
    if "youtube.com" in parsed.netloc and parsed.path == "/watch":
        query_params = parse_qs(parsed.query)
        video_id = query_params.get("v", [None])[0]
    
    # Format: youtu.be/VIDEO_ID
    elif "youtu.be" in parsed.netloc:
        video_id = parsed.path.lstrip("/").split("/")[0].split("?")[0]
    
    # Format: youtube.com/shorts/VIDEO_ID
    elif "youtube.com" in parsed.netloc and "/shorts/" in parsed.path:
        video_id = parsed.path.split("/shorts/")[1].split("/")[0].split("?")[0]
    
    # Format: youtube.com/embed/VIDEO_ID
    elif "youtube.com" in parsed.netloc and "/embed/" in parsed.path:
        video_id = parsed.path.split("/embed/")[1].split("/")[0].split("?")[0]
    
    if not video_id:
        return {"valid": False, "error": "Could not extract video ID from URL"}
    
    # Validate video ID format (11 characters, alphanumeric + - and _)
    if not re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
        return {"valid": False, "error": f"Invalid video ID format: {video_id}"}
    
    return {"valid": True, "video_id": video_id, "url": url}


def validate_media_type(media_type: str | None) -> Dict[str, Any]:
    """Validate media_type parameter.
    
    Args:
        media_type: Type of media to download
        
    Returns:
        {"valid": bool, "error": str (if invalid), "media_type": str (normalized)}
    """
    if media_type is None:
        return {"valid": True, "media_type": "audio"}  # Default
    
    media_type = media_type.strip().lower()
    
    if media_type not in ["audio", "video", "both"]:
        return {
            "valid": False,
            "error": f"media_type must be 'audio', 'video', or 'both' (got: {media_type})"
        }
    
    return {"valid": True, "media_type": media_type}


def validate_quality(quality: str | None) -> Dict[str, Any]:
    """Validate quality parameter.
    
    Args:
        quality: Video quality
        
    Returns:
        {"valid": bool, "error": str (if invalid), "quality": str (normalized)}
    """
    if quality is None:
        return {"valid": True, "quality": "best"}  # Default
    
    quality = quality.strip().lower()
    
    if quality not in ["best", "720p", "480p", "360p"]:
        return {
            "valid": False,
            "error": f"quality must be 'best', '720p', '480p', or '360p' (got: {quality})"
        }
    
    return {"valid": True, "quality": quality}


def validate_filename(filename: str | None) -> Dict[str, Any]:
    """Validate and sanitize filename.
    
    Args:
        filename: Custom filename (without extension)
        
    Returns:
        {"valid": bool, "error": str (if invalid), "filename": str (sanitized)}
    """
    if filename is None:
        return {"valid": True, "filename": None}  # Will use video title
    
    if not isinstance(filename, str) or not filename.strip():
        return {"valid": False, "error": "filename must be a non-empty string"}
    
    # Sanitize: remove dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename.strip())
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")
    
    if not sanitized:
        return {"valid": False, "error": "filename contains only invalid characters"}
    
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return {"valid": True, "filename": sanitized}


def validate_timeout(timeout: int | None) -> Dict[str, Any]:
    """Validate timeout parameter.
    
    Args:
        timeout: Download timeout in seconds
        
    Returns:
        {"valid": bool, "error": str (if invalid), "timeout": int}
    """
    if timeout is None:
        return {"valid": True, "timeout": 300}  # Default 5 minutes
    
    try:
        timeout = int(timeout)
    except (ValueError, TypeError):
        return {"valid": False, "error": "timeout must be an integer"}
    
    if timeout < 5:
        return {"valid": False, "error": "timeout must be at least 5 seconds"}
    
    if timeout > 600:
        return {"valid": False, "error": "timeout must be at most 600 seconds (10 minutes)"}
    
    return {"valid": True, "timeout": timeout}


def validate_max_duration(max_duration: int | None) -> Dict[str, Any]:
    """Validate max_duration parameter.
    
    Args:
        max_duration: Maximum video duration in seconds
        
    Returns:
        {"valid": bool, "error": str (if invalid), "max_duration": int}
    """
    if max_duration is None:
        return {"valid": True, "max_duration": 7200}  # Default 2 hours
    
    try:
        max_duration = int(max_duration)
    except (ValueError, TypeError):
        return {"valid": False, "error": "max_duration must be an integer"}
    
    if max_duration < 60:
        return {"valid": False, "error": "max_duration must be at least 60 seconds"}
    
    if max_duration > 14400:  # 4 hours
        return {"valid": False, "error": "max_duration must be at most 14400 seconds (4 hours)"}
    
    return {"valid": True, "max_duration": max_duration}
