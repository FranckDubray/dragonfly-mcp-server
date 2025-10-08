"""Utility functions for YouTube download operations."""
from __future__ import annotations
from pathlib import Path
import re


def ensure_docs_video_directory() -> Path:
    """Ensure docs/video/ exists within project root.
    
    Returns:
        Path to docs/video/
    """
    project_root = Path(__file__).parent.parent.parent.parent
    docs_video = project_root / "docs" / "video"
    docs_video.mkdir(parents=True, exist_ok=True)
    return docs_video


def sanitize_title(title: str) -> str:
    """Sanitize video title for use as filename.
    
    Args:
        title: Video title
        
    Returns:
        Sanitized filename-safe string
    """
    # Remove/replace dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', title)
    
    # Replace spaces with underscores
    sanitized = re.sub(r'\s+', '_', sanitized)
    
    # Remove leading/trailing underscores and dots
    sanitized = sanitized.strip("._")
    
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    # Fallback if empty
    if not sanitized:
        sanitized = "youtube_video"
    
    return sanitized


def get_unique_filename(directory: Path, base_name: str, extension: str) -> str:
    """Generate unique filename by adding suffix if file exists.
    
    Args:
        directory: Target directory
        base_name: Base filename (without extension)
        extension: File extension (with dot, e.g., '.mp4')
        
    Returns:
        Unique filename (with extension)
    """
    filename = f"{base_name}{extension}"
    file_path = directory / filename
    
    if not file_path.exists():
        return filename
    
    # Add suffix (_1, _2, etc.)
    counter = 1
    while True:
        filename = f"{base_name}_{counter}{extension}"
        file_path = directory / filename
        
        if not file_path.exists():
            return filename
        
        counter += 1
        
        # Safety: prevent infinite loop
        if counter > 1000:
            raise RuntimeError(f"Too many files with base name '{base_name}'")


def format_duration(seconds: float) -> str:
    """Format duration in seconds to HH:MM:SS.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def format_filesize(bytes_size: int) -> str:
    """Format file size in bytes to human-readable string.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted size string (e.g., "145.7 MB")
    """
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"
