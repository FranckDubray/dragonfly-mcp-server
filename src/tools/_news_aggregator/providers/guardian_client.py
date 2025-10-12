"""The Guardian API client."""
import os
import requests
from typing import Dict, Any


class GuardianClient:
    """Client for The Guardian Open Platform API."""
    
    def __init__(self):
        self.api_key = os.getenv("GUARDIAN_API_KEY")
        self.base_url = "https://content.guardianapis.com"
    
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Guardian API."""
        if not self.api_key:
            return {
                "success": False,
                "error": "GUARDIAN_API_KEY not configured. Get free key at https://open-platform.theguardian.com/access/"
            }
        
        url = f"{self.base_url}{endpoint}"
        params["api-key"] = self.api_key
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 401 or response.status_code == 403:
                return {
                    "success": False,
                    "error": "Invalid GUARDIAN_API_KEY. Check your API key."
                }
            
            if response.status_code == 429:
                return {
                    "success": False,
                    "error": "Guardian API rate limit exceeded"
                }
            
            if not response.ok:
                return {
                    "success": False,
                    "error": f"Guardian API HTTP {response.status_code}: {response.text[:200]}"
                }
            
            data = response.json()
            
            if data.get("response", {}).get("status") != "ok":
                return {
                    "success": False,
                    "error": f"Guardian API error: {data.get('message', 'Unknown error')}"
                }
            
            return {"success": True, **data}
            
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Guardian API request timeout after 30 seconds"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Cannot connect to Guardian API. Check internet connection."}
        except Exception as e:
            return {"success": False, "error": f"Guardian API request failed: {str(e)}"}
    
    def search(
        self,
        query: str,
        from_date: str = None,
        to_date: str = None,
        page: int = 1,  # Guardian uses 1-based pages
        page_size: int = 10
    ) -> Dict[str, Any]:
        """Search Guardian articles."""
        params = {
            "q": query,
            "page": page,
            "page-size": min(page_size, 50),  # Guardian max = 50
            "show-fields": "all",  # Get full article data
            "order-by": "newest"
        }
        
        # Guardian uses YYYY-MM-DD format
        if from_date:
            params["from-date"] = from_date
        if to_date:
            params["to-date"] = to_date
        
        result = self._make_request("/search", params)
        
        # Normalize response structure
        if result.get("success"):
            response = result.get("response", {})
            result["articles"] = response.get("results", [])
            result["totalResults"] = response.get("total", 0)
        
        return result
