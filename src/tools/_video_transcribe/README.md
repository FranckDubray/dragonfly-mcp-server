# Video Transcription Tool

Extract audio from video files and transcribe using Whisper API with parallel processing for optimal performance.

## Features

- **Direct FFmpeg extraction**: extracts audio segments on-the-fly (no persistent temp files)
- **Whisper API integration**: multipart/form-data upload to `/api/v1/audio/transcriptions`
- **Parallel processing**: processes up to 3 chunks simultaneously (3x faster)
- **Time-based segmentation**: `time_start`/`time_end` parameters for large videos
- **Returns JSON**: segments with timestamps + full concatenated text
- **Automatic cleanup**: temp files deleted immediately after each chunk

## Performance

- **Sequential** (before): 3 minutes video → ~65 seconds
- **Parallel x3** (now): 3 minutes video → **~20 seconds** ⚡

## Operations

### transcribe
Extract audio from video and transcribe to text.

**Parameters:**
- `path` (required): Video file path (must be under `docs/video/`)
- `time_start` (optional): Start time in seconds (default: 0)
- `time_end` (optional): End time in seconds (default: video duration)
- `chunk_duration` (optional): Internal chunk size in seconds (default: 60)

**Example:**
```json
{
  "operation": "transcribe",
  "path": "docs/video/conference.mp4",
  "time_start": 0,
  "time_end": 180,
  "chunk_duration": 60
}
```

**Returns:**
```json
{
  "success": true,
  "video_path": "docs/video/conference.mp4",
  "time_start": 0,
  "time_end": 180,
  "duration_processed": 180,
  "segments": [
    {"start": 0, "end": 60, "text": "First minute transcription..."},
    {"start": 60, "end": 120, "text": "Second minute transcription..."},
    {"start": 120, "end": 180, "text": "Third minute transcription..."}
  ],
  "full_text": "Complete concatenated transcription...",
  "metadata": {
    "total_segments": 3,
    "video_duration_total": 182.5,
    "audio_codec": "aac",
    "chunk_duration": 60,
    "parallel_processing": true,
    "max_workers": 3
  }
}
```

### get_info
Get video metadata (duration, audio codec, etc.).

**Parameters:**
- `path` (required): Video file path

**Example:**
```json
{
  "operation": "get_info",
  "path": "docs/video/conference.mp4"
}
```

**Returns:**
```json
{
  "success": true,
  "path": "docs/video/conference.mp4",
  "duration": 182.93,
  "duration_formatted": "00:03:02.930",
  "audio_codec": "aac",
  "has_audio": true
}
```

## Use Cases

### Short video (complete transcription)
```json
{
  "operation": "transcribe",
  "path": "docs/video/demo.mp4"
}
```
Processes the entire video in parallel chunks.

### Large video (segmented processing)
For a 10-hour video, process in segments to avoid timeouts:

```json
// First hour
{"path": "...", "time_start": 0, "time_end": 3600}

// Second hour
{"path": "...", "time_start": 3600, "time_end": 7200}

// Third hour
{"path": "...", "time_start": 7200, "time_end": 10800}
```

Each call processes up to 60 chunks (1 hour) in batches of 3.

## Architecture

```
_video_transcribe/
  __init__.py           # Export spec()
  api.py                # Route operations to handlers
  core.py               # Parallel processing orchestration
  audio_extractor.py    # FFmpeg segment extraction
  whisper_client.py     # Whisper API multipart client
  validators.py         # Input validation (path, time ranges)
  utils.py              # Helpers (ffprobe, time formatting)
```

## Configuration

Required environment variables:
- `AI_PORTAL_TOKEN`: API token for Whisper endpoint
- `LLM_ENDPOINT`: Base URL (default: `https://ai.dragonflygroup.fr`)

## Security

- **Chroot**: Video files must be under `docs/video/`
- **Temp files**: Created in system temp dir, deleted immediately after use
- **Input validation**: Path, time ranges, chunk duration strictly validated
- **No persistent data**: All processing is in-memory/temporary

## Dependencies

- FFmpeg (system): for audio extraction
- Python: `requests` for HTTP multipart upload

## Error Handling

All errors return explicit messages:
```json
{
  "error": "Video file not found: docs/video/missing.mp4"
}
```

Common errors:
- Video not found
- No audio stream in video
- FFmpeg not installed
- Whisper API authentication failed
- Invalid time ranges

## Performance Optimization

**Parallel processing workflow:**
1. Calculate chunks (e.g., 0-60s, 60-120s, 120-180s, 180-240s)
2. Process in batches of 3:
   - Batch 1: chunks [0, 1, 2] in parallel
   - Batch 2: chunk [3] alone
3. Collect results and sort by index
4. Return assembled transcript

**Speed gain:** ~3x faster than sequential processing.
