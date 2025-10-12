"""NewsAPI.org client."""
import os
import requests
from typing import Dict, Any, List


class NewsAPIClient:
    """Client for NewsAPI.org (https://newsapi.org/)"""
    
    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2"
    
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to NewsAPI."""
        if not self.api_key:
            return {
                "success": False,
                "error": "NEWS_API_KEY not configured. Get free key at https://newsapi.org/register"
            }
        
        url = f"{self.base_url}{endpoint}"
        params["apiKey"] = self.api_key
        
        # DEBUG: Log request
        debug_params = {k: v for k, v in params.items() if k != "apiKey"}
        print(f"🔍 NewsAPI Request: {endpoint}")
        print(f"   Parameters: {debug_params}")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            # DEBUG: Log response status
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 401:
                return {
                    "success": False,
                    "error": "Invalid NEWS_API_KEY. Check your API key at https://newsapi.org/account"
                }
            
            if response.status_code == 426:
                return {
                    "success": False,
                    "error": "NewsAPI Upgrade Required: This endpoint requires a paid plan. Free tier has limitations."
                }
            
            if response.status_code == 429:
                return {
                    "success": False,
                    "error": "NewsAPI rate limit exceeded (100 requests/day on free tier)"
                }
            
            if not response.ok:
                error_text = response.text[:500]
                print(f"   ❌ Error response: {error_text}")
                return {
                    "success": False,
                    "error": f"NewsAPI HTTP {response.status_code}: {error_text}"
                }
            
            data = response.json()
            
            # DEBUG: Log response data
            print(f"   Response status field: {data.get('status')}")
            print(f"   Total results: {data.get('totalResults', 0)}")
            print(f"   Articles count: {len(data.get('articles', []))}")
            if data.get('message'):
                print(f"   API Message: {data.get('message')}")
            
            if data.get("status") != "ok":
                return {
                    "success": False,
                    "error": f"NewsAPI error: {data.get('message', 'Unknown error')}",
                    "code": data.get("code"),
                    "raw_response": data
                }
            
            # Add debug info to successful response
            result = {"success": True, **data}
            if data.get('totalResults', 0) == 0:
                result["debug_info"] = {
                    "message": "NewsAPI returned 0 results. This could mean:",
                    "reasons": [
                        "No articles match your criteria",
                        "Date range too narrow or in future",
                        "Source/country combination has no content",
                        "Free tier limitation (only recent articles)"
                    ],
                    "endpoint": endpoint,
                    "params_sent": debug_params
                }
            
            return result
            
        except requests.exceptions.Timeout:
            return {"success": False, "error": "NewsAPI request timeout after 30 seconds"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Cannot connect to NewsAPI. Check internet connection."}
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            return {"success": False, "error": f"NewsAPI request failed: {str(e)}"}
    
    def search(
        self,
        query: str,
        from_date: str = None,
        to_date: str = None,
        language: str = None,
        sort_by: str = "publishedAt",
        sources: List[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Search articles with /everything endpoint.
        
        Important: NewsAPI constraints:
        - Cannot use 'sources' with 'language' or 'country'
        - Sources must be valid IDs from /sources endpoint
        """
        params = {
            "q": query,
            "sortBy": sort_by,
            "page": page,
            "pageSize": min(page_size, 100)  # NewsAPI max = 100
        }
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        
        # CRITICAL: sources and language are mutually exclusive in NewsAPI
        if sources:
            # When sources are specified, language is ignored
            params["sources"] = ",".join(sources)
        elif language:
            # Only use language if no sources specified
            params["language"] = language
        
        return self._make_request("/everything", params)
    
    def top_headlines(
        self,
        country: str = None,
        category: str = None,
        query: str = None,
        sources: List[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get top headlines with /top-headlines endpoint.
        
        Important: NewsAPI constraints:
        - Cannot use 'sources' with 'country' or 'category'
        """
        params = {
            "page": page,
            "pageSize": min(page_size, 100)
        }
        
        # CRITICAL: sources and country/category are mutually exclusive
        if sources:
            # When sources are specified, country and category are ignored
            params["sources"] = ",".join(sources)
        else:
            # Only use country/category if no sources specified
            if country:
                params["country"] = country
            if category:
                params["category"] = category
        
        if query:
            params["q"] = query
        
        return self._make_request("/top-headlines", params)
    
    def sources(
        self,
        category: str = None,
        language: str = None,
        country: str = None
    ) -> Dict[str, Any]:
        """Get available sources with /sources endpoint."""
        params = {}
        
        if category:
            params["category"] = category
        if language:
            params["language"] = language
        if country:
            params["country"] = country
        
        return self._make_request("/top-headlines/sources", params)
