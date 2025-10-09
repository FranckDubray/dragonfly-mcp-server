# YouTube Search Tool

Search YouTube videos, channels, and playlists using YouTube Data API v3 (official API).

## Features

- **Search videos**: Find videos by keyword with various filters
- **Search channels**: Find YouTube channels
- **Search playlists**: Find public playlists
- **Get video details**: Retrieve detailed information about specific videos
- **Get trending videos**: Find trending videos by region and category
- **Official API**: Stable, reliable, and documented by Google

## API Key Setup

### 1. Get a Free API Key

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project (or select existing)
3. Enable **YouTube Data API v3**
4. Create credentials → API Key
5. (Optional) Restrict API key to YouTube Data API v3

### 2. Add to .env

```bash
YOUTUBE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### 3. Quota Information

- **Free quota**: 10,000 units per day
- **Search operation**: 100 units (~100 searches/day)
- **Video details**: 1 unit (~10,000 requests/day)
- **Quota resets**: Midnight Pacific Time (PST/PDT)

## Operations

### search

Find videos, channels, or playlists by keyword.

**Parameters:**
- `query` (required): Search query
- `max_results` (optional): Number of results (1-50, default: 10)
- `type` (optional): Type of results - `video`, `channel`, `playlist` (default: `video`)
- `order` (optional): Sort order - `date`, `rating`, `relevance`, `title`, `viewCount` (default: `relevance`)
- `region_code` (optional): 2-letter country code (default: `US`)
- `safe_search` (optional): Safe search mode - `none`, `moderate`, `strict` (default: `none`)

**Example:**
```json
{
  "operation": "search",
  "query": "Python tutorial",
  "max_results": 10,
  "type": "video",
  "order": "viewCount",
  "region_code": "US"
}
```

**Returns:**
```json
{
  "success": true,
  "query": "Python tutorial",
  "total_results": 1000000,
  "results_count": 10,
  "items": [
    {
      "type": "video",
      "id": "rfscVS0vtbw",
      "title": "Learn Python - Full Course for Beginners",
      "description": "This course will give you a full introduction...",
      "channel_title": "freeCodeCamp.org",
      "channel_id": "UC8butISFwT-Wl7EV0hUK0BQ",
      "published_at": "2018-07-11T18:33:27Z",
      "thumbnail": "https://i.ytimg.com/vi/rfscVS0vtbw/mqdefault.jpg",
      "url": "https://www.youtube.com/watch?v=rfscVS0vtbw"
    }
  ]
}
```

### get_video_details

Get detailed information about a specific video.

**Parameters:**
- `video_id` (required): YouTube video ID (11 characters)

**Example:**
```json
{
  "operation": "get_video_details",
  "video_id": "dQw4w9WgXcQ"
}
```

**Returns:**
```json
{
  "success": true,
  "video_id": "dQw4w9WgXcQ",
  "title": "Rick Astley - Never Gonna Give You Up",
  "description": "The official video for "Never Gonna Give You Up"...",
  "channel_title": "Rick Astley",
  "channel_id": "UCuAXFkgsw1L7xaCfnd5JJOw",
  "published_at": "2009-10-25T06:57:33Z",
  "duration": "PT3M33S",
  "view_count": 1234567890,
  "like_count": 12345678,
  "comment_count": 1234567,
  "tags": ["rick astley", "Never Gonna Give You Up", "..."],
  "category_id": "10",
  "thumbnails": {...},
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

### get_trending

Get trending videos by region and category.

**Parameters:**
- `max_results` (optional): Number of results (1-50, default: 10)
- `region_code` (optional): 2-letter country code (default: `US`)
- `category_id` (optional): Category ID (e.g., `10` for Music)

**Common Category IDs:**
- `10`: Music
- `20`: Gaming
- `24`: Entertainment
- `25`: News & Politics
- `28`: Science & Technology

**Example:**
```json
{
  "operation": "get_trending",
  "region_code": "FR",
  "max_results": 10,
  "category_id": "10"
}
```

**Returns:**
```json
{
  "success": true,
  "region": "FR",
  "category_id": "10",
  "results_count": 10,
  "items": [
    {
      "video_id": "...",
      "title": "Trending Music Video",
      "channel_title": "Artist Channel",
      "published_at": "2024-01-15T12:00:00Z",
      "view_count": 10000000,
      "like_count": 500000,
      "url": "https://www.youtube.com/watch?v=...",
      "thumbnail": "https://i.ytimg.com/vi/.../mqdefault.jpg"
    }
  ]
}
```

## Use Cases

### 1. Find and Download Videos

```bash
# 1. Search for videos
{
  "tool": "youtube_search",
  "params": {
    "operation": "search",
    "query": "AI conference 2024",
    "max_results": 5
  }
}

# 2. Download best video (use video_id from search results)
{
  "tool": "youtube_download",
  "params": {
    "operation": "download",
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "media_type": "audio"
  }
}

# 3. Transcribe audio
{
  "tool": "video_transcribe",
  "params": {
    "operation": "transcribe",
    "path": "docs/video/ai_conference_2024.mp3"
  }
}
```

### 2. Research Trending Topics

```bash
# Get trending tech videos in France
{
  "tool": "youtube_search",
  "params": {
    "operation": "get_trending",
    "region_code": "FR",
    "category_id": "28",
    "max_results": 20
  }
}
```

### 3. Channel Discovery

```bash
# Find educational channels
{
  "tool": "youtube_search",
  "params": {
    "operation": "search",
    "query": "Python programming",
    "type": "channel",
    "max_results": 10
  }
}
```

## Error Handling

All operations return explicit error messages:

```json
{
  "error": "YouTube API quota exceeded. Daily limit: 10,000 units. Resets at midnight Pacific Time."
}
```

Common errors:
- Missing or invalid API key
- Quota exceeded (wait until midnight PT)
- Invalid video ID
- Invalid region code
- Network errors

## Architecture

```
_youtube_search/
  __init__.py           # Export spec()
  api.py                # Route operations to handlers
  core.py               # Business logic (search, details, trending)
  validators.py         # Input validation
  services/
    youtube_api.py      # YouTube Data API v3 client
```

## Quota Management

To optimize quota usage:

1. **Cache results**: Store search results locally for repeated queries
2. **Use video details sparingly**: Only fetch details when needed (1 unit vs 100 units for search)
3. **Batch operations**: Group multiple searches in one session
4. **Monitor usage**: Check quota usage at [Google Cloud Console](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)

## Security

- ✅ API key stored in `.env` (never exposed in code)
- ✅ API key validation at initialization
- ✅ Input sanitization and validation
- ✅ No user authentication required (public data only)
- ✅ Quota limits prevent abuse

## Dependencies

- `requests`: HTTP client for YouTube API

## Links

- [YouTube Data API v3 Documentation](https://developers.google.com/youtube/v3)
- [API Key Setup Guide](https://developers.google.com/youtube/registering_an_application)
- [Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)
- [Category IDs](https://developers.google.com/youtube/v3/docs/videoCategories/list)
