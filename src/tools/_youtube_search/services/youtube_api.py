"""YouTube Data API v3 client with fallback token logic."""

import os
import requests
from typing import Dict, Any, List, Optional


class YouTubeAPIClient:
    """Client for YouTube Data API v3."""
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self):
        """Initialize YouTube API client with token fallback."""
        # Try specific key first
        self.api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
        if not self.api_key:
            # Fallback to generic Google key
            self.api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        
        if not self.api_key:
            raise ValueError(
                "Missing Google API token. Set either YOUTUBE_API_KEY or GOOGLE_API_KEY in .env. "
                "Get a free API key at: https://console.developers.google.com/"
            )
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "video",
        order: str = "relevance",
        region_code: str = "US",
        safe_search: str = "none",
        channel_id: Optional[str] = None,
        published_after: Optional[str] = None,
        published_before: Optional[str] = None,
        include_statistics: bool = True
    ) -> Dict[str, Any]:
        """Search YouTube content.
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-50)
            search_type: Type of results (video, channel, playlist)
            order: Sort order (date, rating, relevance, title, viewCount)
            region_code: Region code (e.g., US, FR)
            safe_search: Safe search mode (none, moderate, strict)
            channel_id: Filter to specific channel (optional)
            published_after: Filter videos after date (optional, ISO 8601)
            published_before: Filter videos before date (optional, ISO 8601)
            include_statistics: Fetch view count, likes, duration (costs +1 API unit per result)
            
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
        
        # Add optional filters
        if channel_id:
            params["channelId"] = channel_id
        if published_after:
            params["publishedAfter"] = published_after
        if published_before:
            params["publishedBefore"] = published_before
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Parse results
            items = []
            for item in data.get("items", []):
                parsed_item = self._parse_search_item(item)
                items.append(parsed_item)
            
            # Enrich with statistics if requested and type is video
            if include_statistics and search_type == "video" and items:
                video_ids = [item["id"] for item in items if item.get("type") == "video"]
                if video_ids:
                    statistics = self._get_videos_statistics(video_ids)
                    # Merge statistics into items
                    for item in items:
                        if item["id"] in statistics:
                            item.update(statistics[item["id"]])
            
            return {
                "success": True,
                "query": query,
                "total_results": data.get("pageInfo", {}).get("totalResults", 0),
                "results_count": len(items),
                "items": items
            }
            
        except requests.exceptions.HTTPError as e:
            # Try to get detailed error message from response
            try:
                error_data = e.response.json()
                error_details = error_data.get('error', {})
                error_msg = error_details.get('message', 'Unknown error')
                error_code = error_details.get('code', e.response.status_code)
                
                if error_code == 403:
                    if "quotaExceeded" in str(error_data):
                        error_msg = "YouTube API quota exceeded. Daily limit: 10,000 units. Resets at midnight Pacific Time."
                    else:
                        error_msg = f"YouTube API error 403: {error_msg}. Check your API key and ensure YouTube Data API v3 is enabled."
                elif error_code == 400:
                    error_msg = f"YouTube API error 400: {error_msg}. Check your API key is valid and YouTube Data API v3 is enabled in Google Cloud Console."
                
                raise RuntimeError(f"{error_msg} (HTTP {error_code})")
            except (ValueError, KeyError):
                raise RuntimeError(f"YouTube API error: {e.response.status_code} - {e.response.text[:200]}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {str(e)}")
    
    def _get_videos_statistics(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get statistics for multiple videos in one batch call.
        
        Args:
            video_ids: List of video IDs (max 50)
            
        Returns:
            Dict mapping video_id to statistics
        """
        if not video_ids:
            return {}
        
        # YouTube API allows max 50 IDs per request
        video_ids = video_ids[:50]
        
        url = f"{self.BASE_URL}/videos"
        params = {
            "part": "contentDetails,statistics",
            "id": ",".join(video_ids),
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            result = {}
            for item in data.get("items", []):
                video_id = item.get("id", "")
                statistics = item.get("statistics", {})
                content_details = item.get("contentDetails", {})
                
                result[video_id] = {
                    "view_count": int(statistics.get("viewCount", 0)),
                    "like_count": int(statistics.get("likeCount", 0)),
                    "comment_count": int(statistics.get("commentCount", 0)),
                    "duration": content_details.get("duration", "")
                }
            
            return result
            
        except Exception:
            # If statistics fetch fails, return empty dict (don't fail the whole search)
            return {}
    
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
            try:
                error_data = e.response.json()
                error_details = error_data.get('error', {})
                error_msg = error_details.get('message', 'Unknown error')
                error_code = error_details.get('code', e.response.status_code)
                raise RuntimeError(f"YouTube API error {error_code}: {error_msg}")
            except (ValueError, KeyError):
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
            try:
                error_data = e.response.json()
                error_details = error_data.get('error', {})
                error_msg = error_details.get('message', 'Unknown error')
                error_code = error_details.get('code', e.response.status_code)
                raise RuntimeError(f"YouTube API error {error_code}: {error_msg}")
            except (ValueError, KeyError):
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
