"""
Chess.com API HTTP client
"""
import time
import os
import sys
import logging
from typing import Any, Dict

# Import the existing http_client tool
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from _http_client.core import execute_request

logger = logging.getLogger(__name__)


class ChessComClient:
    """HTTP client for Chess.com PubAPI"""
    
    BASE_URL = "https://api.chess.com"
    USER_AGENT = "dragonfly-mcp-server/1.0 (contact: mcp@dragonflygroup.fr)"
    
    def __init__(self):
        self.last_request_time = 0
        # Rate limiting: 100ms between requests (recommended by Chess.com)
        self.min_delay = float(os.environ.get('CHESS_COM_RATE_LIMIT_DELAY', '0.1'))
    
    def get(self, endpoint: str) -> Dict[str, Any]:
        """
        Execute GET request to Chess.com API
        
        Args:
            endpoint: API endpoint path (e.g., '/pub/player/hikaru')
        
        Returns:
            Dict with response data
        
        Raises:
            Exception: On API errors
        """
        # Rate limiting: wait min_delay between requests
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            delay = self.min_delay - elapsed
            logger.debug(f"Rate limiting: waiting {delay:.2f}s before request to {endpoint}")
            time.sleep(delay)
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            logger.debug(f"Chess.com API request: GET {endpoint}")
            
            result = execute_request(
                method='GET',
                url=url,
                headers={
                    'User-Agent': self.USER_AGENT,
                    'Accept': 'application/json',
                },
                timeout=30,
                max_retries=2,
                retry_delay=1.0,
                response_format='json',
            )
            
            self.last_request_time = time.time()
            
            status = result.get('status_code')
            
            # Handle specific HTTP errors
            if status == 429:
                logger.warning(f"Rate limit exceeded for {endpoint}")
                raise Exception("Rate limit exceeded. Chess.com API is throttling requests. Please slow down.")
            
            if status == 404:
                logger.info(f"Resource not found: {endpoint}")
                raise Exception(f"Resource not found: {endpoint}. The requested player/club/tournament may not exist.")
            
            if status == 410:
                logger.info(f"Resource permanently deleted: {endpoint}")
                raise Exception(f"Resource permanently deleted: {endpoint}")
            
            if status >= 500:
                logger.error(f"Chess.com API server error: HTTP {status} for {endpoint}")
                raise Exception(f"Chess.com API server error (HTTP {status}). Please try again later.")
            
            if status != 200:
                error_msg = result.get('body', {}).get('message', 'Unknown error')
                logger.error(f"Chess.com API error: HTTP {status} - {error_msg}")
                raise Exception(f"HTTP {status}: {error_msg}")
            
            logger.info(f"Chess.com API success: {endpoint} (HTTP {status})")
            return result.get('body', {})
        
        except Exception as e:
            # Re-raise with context
            error_str = str(e)
            if 'not found' in error_str.lower() or '404' in error_str:
                raise Exception(f"Resource not found: {endpoint}")
            raise Exception(f"Chess.com API error: {error_str}")
