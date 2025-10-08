"""Core business logic for YouTube download operations."""
from __future__ import annotations
from typing import Dict, Any

from .validators import (
    validate_youtube_url,
    validate_media_type,
    validate_quality,
    validate_filename,
    validate_timeout,
    validate_max_duration,
)
from .utils import (
    ensure_docs_video_directory,
    sanitize_title,
    get_unique_filename,
    format_duration,
    format_filesize,
)
from .services.downloader import get_video_info, download_media


def handle_get_info(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Get video metadata without downloading.
    
    Args:
        url: YouTube video URL
        timeout: Request timeout
        
    Returns:
        Operation result with metadata or error
    """
    # Validate URL
    url_result = validate_youtube_url(url)
    if not url_result["valid"]:
        return {"error": url_result["error"]}
    
    # Validate timeout
    timeout_result = validate_timeout(timeout)
    if not timeout_result["valid"]:
        return {"error": timeout_result["error"]}
    
    # Get info
    info_result = get_video_info(url, timeout_result["timeout"])
    if not info_result["success"]:
        return {"error": info_result["error"]}
    
    info = info_result["info"]
    
    # Format response
    return {
        "success": True,
        "url": url,
        "video_id": info.get("video_id"),
        "title": info.get("title"),
        "description": info.get("description", "")[:500],  # Truncate long descriptions
        "duration": info.get("duration"),
        "duration_formatted": format_duration(info.get("duration", 0)),
        "uploader": info.get("uploader"),
        "channel": info.get("channel"),
        "upload_date": info.get("upload_date"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "thumbnail": info.get("thumbnail"),
        "formats_available": info.get("formats_available"),
    }


def handle_download(
    url: str,
    media_type: str = "audio",
    quality: str = "best",
    filename: str = None,
    max_duration: int = 7200,
    timeout: int = 300
) -> Dict[str, Any]:
    """Download video/audio from YouTube.
    
    Args:
        url: YouTube video URL
        media_type: "audio", "video", or "both"
        quality: Video quality ("best", "720p", "480p", "360p")
        filename: Custom filename (without extension)
        max_duration: Maximum video duration in seconds
        timeout: Download timeout
        
    Returns:
        Operation result with file info or error
    """
    # Validate all inputs
    url_result = validate_youtube_url(url)
    if not url_result["valid"]:
        return {"error": url_result["error"]}
    
    media_type_result = validate_media_type(media_type)
    if not media_type_result["valid"]:
        return {"error": media_type_result["error"]}
    
    quality_result = validate_quality(quality)
    if not quality_result["valid"]:
        return {"error": quality_result["error"]}
    
    filename_result = validate_filename(filename)
    if not filename_result["valid"]:
        return {"error": filename_result["error"]}
    
    timeout_result = validate_timeout(timeout)
    if not timeout_result["valid"]:
        return {"error": timeout_result["error"]}
    
    max_duration_result = validate_max_duration(max_duration)
    if not max_duration_result["valid"]:
        return {"error": max_duration_result["error"]}
    
    # Get video info first to check duration and get title
    info_result = get_video_info(url, 30)
    if not info_result["success"]:
        return {"error": f"Failed to get video info: {info_result['error']}"}
    
    info = info_result["info"]
    
    # Check duration
    video_duration = info.get("duration", 0)
    if video_duration > max_duration_result["max_duration"]:
        return {
            "error": f"Video is too long ({format_duration(video_duration)}). Maximum allowed: {format_duration(max_duration_result['max_duration'])}"
        }
    
    # Determine output filename
    if filename_result["filename"]:
        base_filename = filename_result["filename"]
    else:
        # Use sanitized video title
        base_filename = sanitize_title(info.get("title", "youtube_video"))
    
    # Ensure output directory exists
    docs_video = ensure_docs_video_directory()
    
    # Generate unique filename(s)
    # Note: yt-dlp will add extensions, so we just pass the base name
    # The unique naming will be handled per file type
    
    # Download
    download_result = download_media(
        url=url,
        output_dir=docs_video,
        filename=base_filename,
        media_type=media_type_result["media_type"],
        quality=quality_result["quality"],
        timeout=timeout_result["timeout"]
    )
    
    if not download_result["success"]:
        return {"error": download_result["error"]}
    
    # Format response
    files = download_result["files"]
    
    # Add human-readable sizes
    for file_info in files:
        file_info["size_formatted"] = format_filesize(file_info["size_bytes"])
        file_info["duration_formatted"] = format_duration(file_info.get("duration", 0))
    
    response = {
        "success": True,
        "url": url,
        "video_id": info.get("video_id"),
        "title": info.get("title"),
        "uploader": info.get("uploader"),
        "duration": video_duration,
        "duration_formatted": format_duration(video_duration),
        "media_type": media_type_result["media_type"],
        "quality": quality_result["quality"],
        "files": files,
    }
    
    # Add convenient shortcuts if only one file
    if len(files) == 1:
        response["file"] = files[0]
    
    return response
