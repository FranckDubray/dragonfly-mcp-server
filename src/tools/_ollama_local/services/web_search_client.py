"""Ollama web search client."""
import requests
import json
from typing import Dict, Any
from ..utils import OLLAMA_WEB_SEARCH_URL, DEFAULT_WEB_SEARCH_TIMEOUT, get_web_search_token, truncate_text


class OllamaWebSearchClient:
    """Client for Ollama web search API (ollama.com/api/web_search)."""
    
    def __init__(self, base_url: str = OLLAMA_WEB_SEARCH_URL):
        self.base_url = base_url
    
    def search(self, query: str, max_results: int = 5, timeout: int = DEFAULT_WEB_SEARCH_TIMEOUT) -> Dict[str, Any]:
        """Search the web using Ollama cloud API."""
        token = get_web_search_token()
        
        if not token:
            return {
                "success": False,
                "error": "OLLAMA_WEB_SEARCH_TOKEN not set in environment"
            }
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query
        }
        
        # Add max_results if supported (might not be in current API)
        if max_results != 5:  # Only add if different from default
            payload["max_results"] = max_results
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            # Check for authentication errors
            if response.status_code == 401:
                return {
                    "success": False,
                    "error": "Invalid OLLAMA_WEB_SEARCH_TOKEN. Check your token.",
                    "status_code": 401
                }
            
            if response.status_code == 403:
                return {
                    "success": False,
                    "error": "Access forbidden. Check your Ollama account permissions.",
                    "status_code": 403
                }
            
            if not response.ok:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
            
            # Parse response
            try:
                data = response.json()
                
                # Extract results
                results = data.get("results", [])
                
                # Limit results to max_results
                if len(results) > max_results:
                    results = results[:max_results]
                
                # Enhance results with metadata
                enhanced_results = []
                for result in results:
                    enhanced = {
                        "title": result.get("title", "No title"),
                        "url": result.get("url", ""),
                        "content": result.get("content", ""),
                        "content_preview": truncate_text(result.get("content", ""), 200)
                    }
                    enhanced_results.append(enhanced)
                
                return {
                    "success": True,
                    "query": query,
                    "results": enhanced_results,
                    "results_count": len(enhanced_results),
                    "total_found": len(data.get("results", [])),
                    "limited_to": max_results,
                    "search_metadata": {
                        "query_length": len(query),
                        "response_time_estimate": f"~{timeout}s max"
                    }
                }
                
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {str(e)}"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to Ollama web search API at {self.base_url}",
                "suggestion": "Check your internet connection"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"Web search timeout after {timeout} seconds",
                "suggestion": "Try a shorter query or increase timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Web search failed: {str(e)}"
            }