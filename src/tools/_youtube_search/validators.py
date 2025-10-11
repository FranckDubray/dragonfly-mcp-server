"""Input validation for youtube_search operations."""

from typing import Dict, Any


def validate_search_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate search operation parameters.
    
    Args:
        params: Search parameters
        
    Returns:
        Validated parameters
        
    Raises:
        ValueError: If validation fails
    """
    query = params.get("query", "").strip()
    if not query:
        raise ValueError("Parameter 'query' is required and cannot be empty")
    
    max_results = params.get("max_results", 10)
    if not isinstance(max_results, int) or max_results < 1 or max_results > 50:
        raise ValueError("Parameter 'max_results' must be an integer between 1 and 50")
    
    search_type = params.get("type", "video")
    valid_types = ["video", "channel", "playlist"]
    if search_type not in valid_types:
        raise ValueError(f"Parameter 'type' must be one of: {', '.join(valid_types)}")
    
    order = params.get("order", "relevance")
    valid_orders = ["date", "rating", "relevance", "title", "viewCount"]
    if order not in valid_orders:
        raise ValueError(f"Parameter 'order' must be one of: {', '.join(valid_orders)}")
    
    # Validate channel_id if provided
    channel_id = params.get("channel_id", "").strip()
    if channel_id and len(channel_id) < 10:
        raise ValueError("Parameter 'channel_id' must be a valid YouTube channel ID (at least 10 characters)")
    
    # Validate published_after/published_before if provided (basic check)
    published_after = params.get("published_after", "").strip()
    if published_after and "T" not in published_after:
        raise ValueError("Parameter 'published_after' must be in ISO 8601 format: 'YYYY-MM-DDTHH:MM:SSZ'")
    
    published_before = params.get("published_before", "").strip()
    if published_before and "T" not in published_before:
        raise ValueError("Parameter 'published_before' must be in ISO 8601 format: 'YYYY-MM-DDTHH:MM:SSZ'")
    
    return {
        "query": query,
        "max_results": max_results,
        "type": search_type,
        "order": order,
        "region_code": params.get("region_code", "US"),
        "safe_search": params.get("safe_search", "none"),
        "channel_id": channel_id if channel_id else None,
        "published_after": published_after if published_after else None,
        "published_before": published_before if published_before else None
    }


def validate_video_details_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate get_video_details operation parameters.
    
    Args:
        params: Video details parameters
        
    Returns:
        Validated parameters
        
    Raises:
        ValueError: If validation fails
    """
    video_id = params.get("video_id", "").strip()
    if not video_id:
        raise ValueError("Parameter 'video_id' is required and cannot be empty")
    
    # Basic validation: YouTube video IDs are typically 11 characters
    if len(video_id) != 11:
        raise ValueError("Parameter 'video_id' must be a valid YouTube video ID (11 characters)")
    
    return {"video_id": video_id}


def validate_trending_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate get_trending operation parameters.
    
    Args:
        params: Trending parameters
        
    Returns:
        Validated parameters
        
    Raises:
        ValueError: If validation fails
    """
    max_results = params.get("max_results", 10)
    if not isinstance(max_results, int) or max_results < 1 or max_results > 50:
        raise ValueError("Parameter 'max_results' must be an integer between 1 and 50")
    
    region_code = params.get("region_code", "US")
    # Basic validation: region codes are typically 2 characters
    if not region_code or len(region_code) != 2:
        raise ValueError("Parameter 'region_code' must be a valid 2-letter country code (e.g., 'US', 'FR')")
    
    category_id = params.get("category_id")
    if category_id is not None:
        if not isinstance(category_id, str) or not category_id.isdigit():
            raise ValueError("Parameter 'category_id' must be a numeric string (e.g., '10' for Music)")
    
    return {
        "max_results": max_results,
        "region_code": region_code.upper(),
        "category_id": category_id
    }
