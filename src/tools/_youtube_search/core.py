"""Core logic for YouTube search operations."""

from typing import Dict, Any
from .services.youtube_api import YouTubeAPIClient
from .validators import (
    validate_search_params,
    validate_video_details_params,
    validate_trending_params
)


def handle_search(**params) -> Dict[str, Any]:
    """Handle search operation.
    
    Args:
        **params: Search parameters
            - query (str): Search query (required)
            - max_results (int): Max results to return (default: 10, max: 50)
            - type (str): Type of results - video, channel, playlist (default: video)
            - order (str): Sort order - date, rating, relevance, title, viewCount (default: relevance)
            - region_code (str): Region code (default: US)
            - safe_search (str): Safe search mode - none, moderate, strict (default: none)
    
    Returns:
        Search results
    """
    try:
        validated = validate_search_params(params)
        client = YouTubeAPIClient()
        
        return client.search(
            query=validated["query"],
            max_results=validated["max_results"],
            search_type=validated["type"],
            order=validated["order"],
            region_code=validated["region_code"],
            safe_search=validated["safe_search"]
        )
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def handle_get_video_details(**params) -> Dict[str, Any]:
    """Handle get_video_details operation.
    
    Args:
        **params: Video details parameters
            - video_id (str): YouTube video ID (required)
    
    Returns:
        Video details
    """
    try:
        validated = validate_video_details_params(params)
        client = YouTubeAPIClient()
        
        return client.get_video_details(validated["video_id"])
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def handle_get_trending(**params) -> Dict[str, Any]:
    """Handle get_trending operation.
    
    Args:
        **params: Trending parameters
            - max_results (int): Max results to return (default: 10, max: 50)
            - region_code (str): Region code (default: US)
            - category_id (str): Category ID (optional, e.g., '10' for Music)
    
    Returns:
        Trending videos
    """
    try:
        validated = validate_trending_params(params)
        client = YouTubeAPIClient()
        
        return client.get_trending(
            max_results=validated["max_results"],
            region_code=validated["region_code"],
            category_id=validated.get("category_id")
        )
        
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
