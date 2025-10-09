"""YouTube Search tool initialization."""

from pathlib import Path
import json


def spec():
    """Load canonical JSON spec for youtube_search tool.
    
    Returns:
        dict: OpenAI function specification
    """
    spec_path = Path(__file__).resolve().parent.parent.parent / "tool_specs" / "youtube_search.json"
    
    if spec_path.exists():
        with open(spec_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Fallback spec if JSON not found
    return {
        "type": "function",
        "function": {
            "name": "youtube_search",
            "displayName": "YouTube Search",
            "description": "Search YouTube videos, channels, and playlists using YouTube Data API v3. Requires YOUTUBE_API_KEY in .env. Free quota: 10,000 units/day (100 units per search = ~100 searches/day).",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["search", "get_video_details", "get_trending"],
                        "description": "Operation to perform"
                    }
                },
                "required": ["operation"],
                "additionalProperties": False
            }
        }
    }
