"""YouTube download service using yt-dlp."""
from __future__ import annotations
from typing import Dict, Any
from pathlib import Path
import yt_dlp


def get_video_info(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Get video metadata without downloading.
    
    Args:
        url: YouTube video URL
        timeout: Request timeout in seconds
        
    Returns:
        {"success": bool, "info": dict (if success), "error": str (if failed)}
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': timeout,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract relevant metadata
            metadata = {
                "video_id": info.get("id"),
                "title": info.get("title"),
                "description": info.get("description", ""),
                "duration": info.get("duration"),  # seconds
                "uploader": info.get("uploader"),
                "upload_date": info.get("upload_date"),  # YYYYMMDD
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "channel": info.get("channel"),
                "channel_id": info.get("channel_id"),
                "thumbnail": info.get("thumbnail"),
                "formats_available": len(info.get("formats", [])),
            }
            
            return {"success": True, "info": metadata}
            
    except yt_dlp.utils.DownloadError as e:
        return {"success": False, "error": f"yt-dlp error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


def download_media(
    url: str,
    output_dir: Path,
    filename: str,
    media_type: str,
    quality: str,
    timeout: int
) -> Dict[str, Any]:
    """Download video/audio from YouTube.
    
    Args:
        url: YouTube video URL
        output_dir: Target directory
        filename: Output filename (without extension)
        media_type: "audio", "video", or "both"
        quality: "best", "720p", "480p", or "360p"
        timeout: Download timeout in seconds
        
    Returns:
        {
            "success": bool,
            "files": list[dict] (if success),
            "error": str (if failed)
        }
    """
    output_template = str(output_dir / filename)
    files_downloaded = []
    
    # Download audio
    if media_type in ["audio", "both"]:
        audio_result = _download_audio(url, output_template, timeout)
        if not audio_result["success"]:
            return audio_result
        files_downloaded.append(audio_result["file"])
    
    # Download video
    if media_type in ["video", "both"]:
        video_result = _download_video(url, output_template, quality, timeout)
        if not video_result["success"]:
            # If audio was already downloaded, note partial success
            if files_downloaded:
                return {
                    "success": False,
                    "error": f"Audio downloaded, but video failed: {video_result['error']}",
                    "files": files_downloaded
                }
            return video_result
        files_downloaded.append(video_result["file"])
    
    return {"success": True, "files": files_downloaded}


def _download_audio(url: str, output_template: str, timeout: int) -> Dict[str, Any]:
    """Download audio-only (MP3).
    
    Args:
        url: YouTube video URL
        output_template: Output path template (without extension)
        timeout: Download timeout
        
    Returns:
        {"success": bool, "file": dict (if success), "error": str (if failed)}
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_template}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': timeout,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Determine actual output filename
            audio_path = Path(f"{output_template}.mp3")
            
            if not audio_path.exists():
                return {"success": False, "error": f"Audio file not found after download: {audio_path}"}
            
            file_info = {
                "type": "audio",
                "filename": audio_path.name,
                "path": str(audio_path),
                "size_bytes": audio_path.stat().st_size,
                "format": "mp3",
                "duration": info.get("duration"),
            }
            
            return {"success": True, "file": file_info}
            
    except yt_dlp.utils.DownloadError as e:
        return {"success": False, "error": f"Audio download failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error during audio download: {str(e)}"}


def _download_video(url: str, output_template: str, quality: str, timeout: int) -> Dict[str, Any]:
    """Download video (MP4).
    
    Args:
        url: YouTube video URL
        output_template: Output path template (without extension)
        quality: "best", "720p", "480p", or "360p"
        timeout: Download timeout
        
    Returns:
        {"success": bool, "file": dict (if success), "error": str (if failed)}
    """
    # Map quality to format selector
    quality_map = {
        "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
        "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best",
        "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best",
    }
    
    format_selector = quality_map.get(quality, quality_map["best"])
    
    ydl_opts = {
        'format': format_selector,
        'outtmpl': f'{output_template}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': timeout,
        'merge_output_format': 'mp4',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Determine actual output filename
            video_path = Path(f"{output_template}.mp4")
            
            if not video_path.exists():
                return {"success": False, "error": f"Video file not found after download: {video_path}"}
            
            file_info = {
                "type": "video",
                "filename": video_path.name,
                "path": str(video_path),
                "size_bytes": video_path.stat().st_size,
                "format": "mp4",
                "duration": info.get("duration"),
                "resolution": f"{info.get('width', 0)}x{info.get('height', 0)}",
                "fps": info.get('fps'),
            }
            
            return {"success": True, "file": file_info}
            
    except yt_dlp.utils.DownloadError as e:
        return {"success": False, "error": f"Video download failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error during video download: {str(e)}"}
