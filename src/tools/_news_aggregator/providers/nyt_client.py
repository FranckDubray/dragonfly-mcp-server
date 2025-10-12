"""New York Times API client."""
import os
import requests
from typing import Dict, Any


class NYTClient:
    """Client for New York Times Article Search API."""
    
    def __init__(self):
        self.api_key = os.getenv("NYT_API_KEY")
        self.base_url = "https://api.nytimes.com/svc/search/v2"
    
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to NYT API."""
        if not self.api_key:
            return {
                "success": False,
                "error": "NYT_API_KEY not configured. Get free key at https://developer.nytimes.com/get-started"
            }
        
        url = f"{self.base_url}{endpoint}"
        params["api-key"] = self.api_key
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 401:
                return {
                    "success": False,
                    "error": "Invalid NYT_API_KEY. Check your API key at https://developer.nytimes.com/my-apps"
                }
            
            if response.status_code == 429:
                return {
                    "success": False,
                    "error": "NYT API rate limit exceeded (1000 requests/day)"
                }
            
            if not response.ok:
                return {
                    "success": False,
                    "error": f"NYT API HTTP {response.status_code}: {response.text[:200]}"
                }
            
            data = response.json()
            
            if data.get("status") != "OK":
                return {
                    "success": False,
                    "error": f"NYT API error: {data.get('message', 'Unknown error')}"
                }
            
            return {"success": True, **data}
            
        except requests.exceptions.Timeout:
            return {"success": False, "error": "NYT API request timeout after 30 seconds"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Cannot connect to NYT API. Check internet connection."}
        except Exception as e:
            return {"success": False, "error": f"NYT API request failed: {str(e)}"}
    
    def search(
        self,
        query: str,
        from_date: str = None,
        to_date: str = None,
        page: int = 0,  # NYT uses 0-based pages
        page_size: int = 10
    ) -> Dict[str, Any]:
        """Search NYT articles."""
        params = {
            "q": query,
            "page": page,
            # NYT doesn't have page_size param, returns 10 by default
        }
        
        # NYT uses YYYYMMDD format (remove hyphens)
        if from_date and isinstance(from_date, str):
            params["begin_date"] = from_date.replace("-", "")
        if to_date and isinstance(to_date, str):
            params["end_date"] = to_date.replace("-", "")
        
        result = self._make_request("/articlesearch.json", params)
        
        # Normalize response structure
        if result.get("success"):
            response = result.get("response", {})
            result["articles"] = response.get("docs", [])
            result["totalResults"] = response.get("meta", {}).get("hits", 0)
        
        return result
