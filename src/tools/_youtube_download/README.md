# YouTube Download Tool

Download videos or audio from YouTube URLs. Perfect integration with `video_transcribe` for content extraction and analysis.

## Features

- **Audio-only download** (MP3, 192kbps) - optimal for transcription
- **Video download** (MP4) with quality selection (best, 720p, 480p, 360p)
- **Dual download** (both audio and video as separate files)
- **Metadata extraction** (title, duration, uploader, views, etc.)
- **Automatic filename generation** from video title
- **Unique naming** (suffixes _1, _2 if file exists)
- **Duration limits** to prevent excessive downloads
- **Timeout control** for network operations

## Operations

### download
Download video and/or audio from YouTube URL.

**Parameters:**
- `url` (required): YouTube video URL (supports various formats)
  - `youtube.com/watch?v=VIDEO_ID`
  - `youtu.be/VIDEO_ID`
  - `youtube.com/shorts/VIDEO_ID`
  - `youtube.com/embed/VIDEO_ID`
- `media_type` (optional): Type of media to download
  - `"audio"` (default): MP3 audio only (best for transcription)
  - `"video"`: MP4 video with audio
  - `"both"`: Separate audio (MP3) and video (MP4) files
- `quality` (optional): Video quality (ignored for audio-only)
  - `"best"` (default): Highest available quality
  - `"720p"`: Max 720p resolution
  - `"480p"`: Max 480p resolution
  - `"360p"`: Max 360p resolution
- `filename` (optional): Custom filename without extension. If omitted, uses sanitized video title
- `max_duration` (optional): Maximum video duration in seconds (default: 7200 = 2 hours, max: 14400 = 4 hours)
- `timeout` (optional): Download timeout in seconds (default: 300, range: 5-600)

**Example (audio only for transcription):**
```json
{
  "operation": "download",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "media_type": "audio",
  "filename": "podcast_episode_42"
}
```

**Returns:**
```json
{
  "success": true,
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "video_id": "dQw4w9WgXcQ",
  "title": "Amazing Podcast Episode",
  "uploader": "Channel Name",
  "duration": 1850,
  "duration_formatted": "30:50",
  "media_type": "audio",
  "quality": "best",
  "file": {
    "type": "audio",
    "filename": "podcast_episode_42.mp3",
    "path": "docs/video/podcast_episode_42.mp3",
    "size_bytes": 24567890,
    "size_formatted": "23.4 MB",
    "format": "mp3",
    "duration": 1850,
    "duration_formatted": "30:50"
  }
}
```

**Example (video with quality):**
```json
{
  "operation": "download",
  "url": "https://youtu.be/dQw4w9WgXcQ",
  "media_type": "video",
  "quality": "720p"
}
```

**Returns:**
```json
{
  "success": true,
  "url": "https://youtu.be/dQw4w9WgXcQ",
  "video_id": "dQw4w9WgXcQ",
  "title": "Amazing Video",
  "uploader": "Channel Name",
  "duration": 215,
  "duration_formatted": "03:35",
  "media_type": "video",
  "quality": "720p",
  "file": {
    "type": "video",
    "filename": "Amazing_Video.mp4",
    "path": "docs/video/Amazing_Video.mp4",
    "size_bytes": 45678901,
    "size_formatted": "43.6 MB",
    "format": "mp4",
    "duration": 215,
    "duration_formatted": "03:35",
    "resolution": "1280x720",
    "fps": 30
  }
}
```

**Example (both audio and video):**
```json
{
  "operation": "download",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "media_type": "both",
  "filename": "conference_2024"
}
```

**Returns:**
```json
{
  "success": true,
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "video_id": "dQw4w9WgXcQ",
  "title": "Tech Conference 2024",
  "uploader": "Tech Channel",
  "duration": 3600,
  "duration_formatted": "01:00:00",
  "media_type": "both",
  "quality": "best",
  "files": [
    {
      "type": "audio",
      "filename": "conference_2024.mp3",
      "path": "docs/video/conference_2024.mp3",
      "size_bytes": 69120000,
      "size_formatted": "65.9 MB",
      "format": "mp3",
      "duration": 3600,
      "duration_formatted": "01:00:00"
    },
    {
      "type": "video",
      "filename": "conference_2024.mp4",
      "path": "docs/video/conference_2024.mp4",
      "size_bytes": 524288000,
      "size_formatted": "500.0 MB",
      "format": "mp4",
      "duration": 3600,
      "duration_formatted": "01:00:00",
      "resolution": "1920x1080",
      "fps": 30
    }
  ]
}
```

### get_info
Get video metadata without downloading.

**Parameters:**
- `url` (required): YouTube video URL
- `timeout` (optional): Request timeout in seconds (default: 30)

**Example:**
```json
{
  "operation": "get_info",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Returns:**
```json
{
  "success": true,
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "video_id": "dQw4w9WgXcQ",
  "title": "Amazing Video Title",
  "description": "First 500 characters of description...",
  "duration": 215,
  "duration_formatted": "03:35",
  "uploader": "Channel Name",
  "channel": "Channel Name",
  "upload_date": "20240115",
  "view_count": 1234567,
  "like_count": 98765,
  "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
  "formats_available": 25
}
```

## Use Cases

### 1. Download for transcription (audio only)
```json
// Step 1: Download audio
{
  "tool": "youtube_download",
  "params": {
    "url": "https://www.youtube.com/watch?v=tech-talk-2024",
    "media_type": "audio"
  }
}
// Returns: {"file": {"path": "docs/video/Tech_Talk_2024.mp3"}}

// Step 2: Transcribe
{
  "tool": "video_transcribe",
  "params": {
    "path": "docs/video/Tech_Talk_2024.mp3"
  }
}
// Returns: Full transcription with timestamps
```

### 2. Check video info before downloading
```json
// Get info first to check duration
{
  "tool": "youtube_download",
  "params": {
    "operation": "get_info",
    "url": "https://www.youtube.com/watch?v=long-conference"
  }
}
// Returns: {"duration": 7200, "duration_formatted": "02:00:00"}

// If acceptable, download
{
  "tool": "youtube_download",
  "params": {
    "url": "https://www.youtube.com/watch?v=long-conference",
    "media_type": "audio"
  }
}
```

### 3. Archive video with custom filename
```json
{
  "tool": "youtube_download",
  "params": {
    "url": "https://www.youtube.com/watch?v=important-video",
    "media_type": "both",
    "quality": "720p",
    "filename": "archive_2024_q1_presentation"
  }
}
// Saves: archive_2024_q1_presentation.mp3 + archive_2024_q1_presentation.mp4
```

## Architecture

```
_youtube_download/
  __init__.py           # Export spec()
  api.py                # Route operations to handlers
  core.py               # Business logic (download, get_info)
  validators.py         # Input validation (URL, media_type, quality, etc.)
  utils.py              # Helpers (sanitize, unique naming, formatting)
  services/
    __init__.py
    downloader.py       # yt-dlp wrapper (video info, audio/video download)
```

## Configuration

**Dependencies:**
- `yt-dlp>=2023.10.0` (YouTube downloader)
- `FFmpeg` (system dependency for audio extraction)

**No environment variables required** - works out of the box!

## Security

- **Chroot**: Files saved only to `docs/video/`
- **URL validation**: Only YouTube domains accepted
- **Filename sanitization**: Path traversal prevention
- **Duration limits**: Prevents downloading excessively long videos
- **Timeout enforcement**: Network operations have hard limits

## Error Handling

All errors return explicit messages:
```json
{
  "error": "Video is too long (03:45:00). Maximum allowed: 02:00:00"
}
```

**Common errors:**
- Invalid YouTube URL format
- Video not found or private
- Duration exceeds max_duration
- Network timeout
- Disk space issues

## Integration with video_transcribe

Perfect workflow for video content analysis:

```bash
# 1. Download YouTube video (audio only, faster)
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "youtube_download",
    "params": {
      "url": "https://www.youtube.com/watch?v=tech-conference",
      "media_type": "audio"
    }
  }'

# Response: {"file": {"path": "docs/video/Tech_Conference.mp3"}}

# 2. Transcribe with Whisper (parallel processing, 3x faster)
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "video_transcribe",
    "params": {
      "path": "docs/video/Tech_Conference.mp3"
    }
  }'

# Response: {"full_text": "Complete transcription...", "segments": [...]}
```

Now you have searchable, analyzable text content from any YouTube video!

## Performance

- **Audio-only**: ~1-5 MB/min (MP3 192kbps)
- **Video 720p**: ~50-100 MB/min (depends on content)
- **Download speed**: Limited by network and YouTube throttling
- **Typical times**:
  - 10-minute video (audio): 10-30 seconds
  - 1-hour video (audio): 1-3 minutes
  - 1-hour video (720p): 5-15 minutes

## Tips

1. **For transcription**: Always use `media_type="audio"` (faster, smaller)
2. **Check duration first**: Use `get_info` before downloading long videos
3. **Custom filenames**: Use descriptive names for better organization
4. **Quality selection**: Lower quality = faster download + smaller size
5. **Batch processing**: Download multiple videos, then transcribe all at once
