"""
Trivia API HTTP client
All I/O operations with Open Trivia Database API
"""
import requests
import time
from typing import Dict, Any, Optional


BASE_URL = "https://opentdb.com"
RATE_LIMIT_DELAY = 5  # seconds to wait on rate limit


class TriviaAPIError(Exception):
    """Custom exception for Trivia API errors"""
    pass


class TriviaAPIClient:
    """HTTP client for Open Trivia Database API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Dragonfly-MCP-Server/1.16.0"
        })
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < 1.0:  # At least 1 second between requests
            time.sleep(1.0 - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retry_on_rate_limit: bool = True
    ) -> Dict[str, Any]:
        """
        Make HTTP GET request to API
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            retry_on_rate_limit: Whether to retry on rate limit error
        
        Returns:
            JSON response data
        
        Raises:
            TriviaAPIError: On API errors
        """
        self._rate_limit()
        
        url = f"{BASE_URL}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for API response code in /api.php responses
            if "response_code" in data:
                code = data["response_code"]
                
                # Rate limit (code 5)
                if code == 5 and retry_on_rate_limit:
                    time.sleep(RATE_LIMIT_DELAY)
                    return self._make_request(endpoint, params, retry_on_rate_limit=False)
                
                # Other error codes
                elif code != 0:
                    from ..utils import parse_response_code
                    error_info = parse_response_code(code)
                    raise TriviaAPIError(f"API error (code {code}): {error_info['message']}")
            
            return data
            
        except requests.exceptions.Timeout:
            raise TriviaAPIError("Request timeout - API did not respond in time")
        except requests.exceptions.ConnectionError:
            raise TriviaAPIError("Connection error - could not reach Open Trivia Database API")
        except requests.exceptions.HTTPError as e:
            raise TriviaAPIError(f"HTTP error {e.response.status_code}: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise TriviaAPIError(f"Request failed: {str(e)}")
        except ValueError as e:
            raise TriviaAPIError(f"Invalid JSON response: {str(e)}")
    
    def get_questions(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get trivia questions
        
        Args:
            query_params: Query parameters for API
        
        Returns:
            API response with questions
        """
        return self._make_request("/api.php", params=query_params)
    
    def list_categories(self) -> Dict[str, Any]:
        """
        Get list of all trivia categories
        
        Returns:
            API response with categories
        """
        return self._make_request("/api_category.php")
    
    def get_category_count(self, category_id: int) -> Dict[str, Any]:
        """
        Get question count for a specific category
        
        Args:
            category_id: Category ID
        
        Returns:
            API response with counts
        """
        return self._make_request("/api_count.php", params={"category": category_id})
    
    def get_global_count(self) -> Dict[str, Any]:
        """
        Get global question count
        
        Returns:
            API response with global counts
        """
        return self._make_request("/api_count.php")
    
    def create_session_token(self) -> Dict[str, Any]:
        """
        Create a new session token
        
        Returns:
            API response with token
        """
        return self._make_request("/api_token.php", params={"command": "request"})
    
    def reset_session_token(self, token: str) -> Dict[str, Any]:
        """
        Reset a session token
        
        Args:
            token: Token to reset
        
        Returns:
            API response
        """
        return self._make_request("/api_token.php", params={"command": "reset", "token": token})
