"""
Discord Bot HTTP client with rate limiting.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import os
import time
import httpx

API_BASE = "https://discord.com/api/v10"

@dataclass
class HttpResult:
    status_code: int
    json: Optional[Dict[str, Any]]
    headers: Dict[str, str]

def get_bot_token() -> str:
    """Get Discord bot token from environment."""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN not configured in .env")
    return token.strip()

def build_headers() -> Dict[str, str]:
    """Build headers for Discord Bot API."""
    token = get_bot_token()
    return {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "DiscordBot (Dragonfly MCP, 1.0)"
    }

def http_request(
    method: str,
    endpoint: str,
    json_body: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    timeout: float = 30.0
) -> HttpResult:
    """
    Execute HTTP request with automatic retry on 429 and 5xx.
    
    Args:
        method: HTTP method (GET/POST/PATCH/DELETE/PUT)
        endpoint: API endpoint (ex: /channels/123/messages)
        json_body: JSON payload
        max_retries: Max retry attempts
        timeout: Request timeout
    
    Returns:
        HttpResult with status_code, json, headers
    """
    url = f"{API_BASE}{endpoint}"
    headers = build_headers()
    backoffs = [0.5, 1.0, 2.0]
    attempt = 0
    
    while True:
        try:
            with httpx.Client() as client:
                resp = client.request(method, url, json=json_body, headers=headers, timeout=timeout)
        except httpx.RequestError as e:
            if attempt >= max_retries - 1:
                raise RuntimeError(f"Discord network error: {e}")
            time.sleep(backoffs[min(attempt, len(backoffs) - 1)])
            attempt += 1
            continue
        
        # Handle 429 Too Many Requests
        if resp.status_code == 429 and attempt < max_retries:
            retry_after = 1.0
            try:
                data = resp.json()
                retry_after = float(data.get("retry_after") or retry_after)
            except Exception:
                ra_hdr = resp.headers.get("Retry-After")
                if ra_hdr:
                    try:
                        retry_after = float(ra_hdr)
                    except Exception:
                        pass
            retry_after = min(retry_after, 60.0)  # Cap at 60s
            time.sleep(retry_after)
            attempt += 1
            continue
        
        # Handle 5xx server errors
        if 500 <= resp.status_code < 600 and attempt < max_retries:
            time.sleep(backoffs[min(attempt, len(backoffs) - 1)])
            attempt += 1
            continue
        
        # Success or non-retryable error
        try:
            js = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else None
        except Exception:
            js = None
        
        return HttpResult(status_code=resp.status_code, json=js, headers=dict(resp.headers))
