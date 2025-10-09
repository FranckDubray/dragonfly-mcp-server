"""YouTube Search - Search YouTube videos, channels, and playlists using YouTube Data API v3.

Requires YOUTUBE_API_KEY in .env. Get a free API key at: https://console.developers.google.com/

Free quota: 10,000 units/day
- Search operation = 100 units (~100 searches per day)
- Video details = 1 unit (~10,000 requests per day)

Example usage:
    # Search for videos
    {
        "tool": "youtube_search",
        "params": {
            "operation": "search",
            "query": "Python tutorial",
            "max_results": 10,
            "type": "video",
            "order": "relevance"
        }
    }
    
    # Get video details
    {
        "tool": "youtube_search",
        "params": {
            "operation": "get_video_details",
            "video_id": "dQw4w9WgXcQ"
        }
    }
    
    # Get trending videos
    {
        "tool": "youtube_search",
        "params": {
            "operation": "get_trending",
            "region_code": "FR",
            "max_results": 10,
            "category_id": "10"
        }
    }

Workflow for video download and transcription:
    1. youtube_search (find videos) → returns video URLs
    2. youtube_download (download audio) → saves to docs/video/
    3. video_transcribe (extract text) → returns transcript
"""
from __future__ import annotations
from typing import Dict, Any

# Import from implementation package
from ._youtube_search.api import route_operation
from ._youtube_search import spec as _spec


def run(operation: str = "search", **params) -> Dict[str, Any]:
    """Execute YouTube search operation.
    
    Args:
        operation: Operation to perform ("search", "get_video_details", "get_trending")
        **params: Operation parameters
        
    Returns:
        Operation result
    """
    # Normalize operation
    op = (operation or params.get("operation") or "search").strip().lower()
    
    # Validate required params for each operation
    if op == "search":
        if not params.get("query"):
            return {"error": "Parameter 'query' is required for search operation"}
    
    elif op == "get_video_details":
        if not params.get("video_id"):
            return {"error": "Parameter 'video_id' is required for get_video_details operation"}
    
    elif op == "get_trending":
        # No required params for get_trending (all have defaults)
        pass
    
    # Route to handler
    return route_operation(op, **params)


def spec() -> Dict[str, Any]:
    """Load canonical JSON spec.
    
    Returns:
        OpenAI function spec
    """
    return _spec()
