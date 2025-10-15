"""
Lichess API HTTP client (public endpoints only)
"""
import time
import os
import sys
import logging
from typing import Any, Dict, Optional

# Reuse existing http_client tool from project
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from _http_client.core import execute_request  # type: ignore

logger = logging.getLogger(__name__)


class LichessClient:
    BASE_URL = "https://lichess.org"
    USER_AGENT = "dragonfly-mcp-server/1.0 (contact: mcp@dragonflygroup.fr)"

    def __init__(self):
        self.last_request_time = 0.0
        self.min_delay = float(os.environ.get('LICHESS_RATE_LIMIT_DELAY', '0.2'))

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        url = f"{self.BASE_URL}{endpoint}"
        try:
            result = execute_request(
                method='GET',
                url=url,
                headers={
                    'User-Agent': self.USER_AGENT,
                    'Accept': 'application/json',
                },
                params=params or {},
                timeout=30,
                max_retries=2,
                retry_delay=1.0,
                response_format='json',
            )
            self.last_request_time = time.time()
            status = result.get('status_code')
            if status == 429:
                raise Exception('Rate limit exceeded')
            if status == 404:
                raise Exception('Resource not found')
            if status and status >= 500:
                raise Exception(f"Server error: HTTP {status}")
            if status != 200:
                body = result.get('body', {})
                message = body.get('error') if isinstance(body, dict) else 'Unknown error'
                raise Exception(f"HTTP {status}: {message}")
            return result.get('body', {})
        except Exception as e:
            msg = str(e)
            if 'not found' in msg.lower() or '404' in msg:
                raise Exception('Resource not found')
            raise
