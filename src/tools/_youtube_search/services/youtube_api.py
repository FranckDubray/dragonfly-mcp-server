"""YouTube Data API v3 client."""

import os
import requests
from typing import Dict, Any, List, Optional


class YouTubeAPIClient:
    """Client for YouTube Data API v3."""
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self):
        """Initialize YouTube API client."""
        self.api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError(
                "YOUTUBE_API_KEY not found in environment variables. "
                "Get a free API key at: https://console.developers.google.com/"
            )
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "video",
        order: str = "relevance",
        region_code: str = "US",
        safe_search: str = "none"
    ) -> Dict[str, Any]:
        """Search YouTube content.
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-50)
            search_type: Type of results (video, channel, playlist)
            order: Sort order (date, rating, relevance, title, viewCount)
            region_code: Region code (e.g., US, FR)
            safe_search: Safe search mode (none, moderate, strict)
            
        Returns:
            Search results with items
            
        Raises:
            RuntimeError: If API request fails
        """
        url = f"{self.BASE_URL}/search"
        params = {
            "part": "snippet",
            "q": query,
            "maxResults": max_results,
            "type": search_type,
            "order": order,
            "regionCode": region_code,
            "safeSearch": safe_search,
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Parse results
            items = []
            for item in data.get("items", []):
                parsed_item = self._parse_search_item(item)
                items.append(parsed_item)
            
            return {
                "success": True,
                "query": query,
                "total_results": data.get("pageInfo", {}).get("totalResults", 0),
                "results_count": len(items),
                "items": items
            }
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"YouTube API error: {e.response.status_code}"
            if e.response.status_code == 403:
                try:
                    error_data = e.response.json()
                    if "quotaExceeded" in str(error_data):
                        error_msg = "YouTube API quota exceeded. Daily limit: 10,000 units. Resets at midnight Pacific Time."
                    else:
                        error_msg = f"YouTube API error 403: {error_data.get('error', {}).get('message', 'Forbidden')}"
                except:
                    error_msg = "YouTube API error 403: Check your API key"
            raise RuntimeError(error_msg)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {str(e)}")
    
    def get_video_details(self, video_id: str) -> Dict[str, Any]:
        """Get detailed information about a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video details
            
        Raises:
            RuntimeError: If API request fails
        """
        url = f"{self.BASE_URL}/videos"
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": video_id,
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            items = data.get("items", [])
            if not items:
                raise RuntimeError(f"Video not found: {video_id}")
            
            video = items[0]
            snippet = video.get("snippet", {})
            statistics = video.get("statistics", {})
            content_details = video.get("contentDetails", {})
            
            return {
                "success": True,
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "channel_id": snippet.get("channelId", ""),
                "published_at": snippet.get("publishedAt", ""),
                "duration": content_details.get("duration", ""),
                "view_count": int(statistics.get("viewCount", 0)),
                "like_count": int(statistics.get("likeCount", 0)),
                "comment_count": int(statistics.get("commentCount", 0)),
                "tags": snippet.get("tags", []),
                "category_id": snippet.get("categoryId", ""),
                "thumbnails": snippet.get("thumbnails", {}),
                "url": f"https://www.youtube.com/watch?v={video_id}"
            }
            
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"YouTube API error: {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {str(e)}")
    
    def get_trending(
        self,
        max_results: int = 10,
        region_code: str = "US",
        category_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get trending videos.
        
        Args:
            max_results: Maximum number of results (1-50)
            region_code: Region code (e.g., US, FR)
            category_id: Category ID (e.g., '10' for Music)
            
        Returns:
            Trending videos
            
        Raises:
            RuntimeError: If API request fails
        """
        url = f"{self.BASE_URL}/videos"
        params = {
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "maxResults": max_results,
            "regionCode": region_code,
            "key": self.api_key
        }
        
        if category_id:
            params["videoCategoryId"] = category_id
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            items = []
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                statistics = item.get("statistics", {})
                video_id = item.get("id", "")
                
                items.append({
                    "video_id": video_id,
                    "title": snippet.get("title", ""),
                    "channel_title": snippet.get("channelTitle", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "view_count": int(statistics.get("viewCount", 0)),
                    "like_count": int(statistics.get("likeCount", 0)),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", "")
                })
            
            return {
                "success": True,
                "region": region_code,
                "category_id": category_id,
                "results_count": len(items),
                "items": items
            }
            
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"YouTube API error: {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {str(e)}")
    
    def _parse_search_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a search result item.
        
        Args:
            item: Raw search item from API
            
        Returns:
            Parsed item with clean structure
        """
        snippet = item.get("snippet", {})
        id_info = item.get("id", {})
        
        # Determine type and ID
        item_type = id_info.get("kind", "").split("#")[-1]  # e.g., "youtube#video" -> "video"
        item_id = id_info.get("videoId") or id_info.get("channelId") or id_info.get("playlistId", "")
        
        # Build URL based on type
        if item_type == "video":
            url = f"https://www.youtube.com/watch?v={item_id}"
        elif item_type == "channel":
            url = f"https://www.youtube.com/channel/{item_id}"
        elif item_type == "playlist":
            url = f"https://www.youtube.com/playlist?list={item_id}"
        else:
            url = ""
        
        return {
            "type": item_type,
            "id": item_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "channel_title": snippet.get("channelTitle", ""),
            "channel_id": snippet.get("channelId", ""),
            "published_at": snippet.get("publishedAt", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "url": url
        }
