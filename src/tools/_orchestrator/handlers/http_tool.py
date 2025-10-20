

# Generic MCP HTTP tool handler (POST /execute with 3-level retry)

import time
import json
from typing import Dict, Any
try:
    import requests
except ImportError:
    requests = None

from .base import AbstractHandler, HandlerError

class HttpToolHandler(AbstractHandler):
    """Generic HTTP tool handler (calls MCP server /execute endpoint)"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip('/')
        self._endpoint = f"{self.base_url}/execute"
    
    @property
    def kind(self) -> str:
        return "http_tool"
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Call MCP tool via POST /execute.
        """
        if requests is None:
            raise HandlerError(
                message="requests library not available",
                code="MISSING_DEPENDENCY",
                category="validation",
                retryable=False
            )
        
        tool_name = kwargs.get('tool')
        if not tool_name:
            raise HandlerError(
                message="Missing required parameter: tool",
                code="INVALID_INPUT",
                category="validation",
                retryable=False
            )
        
        params = {k: v for k, v in kwargs.items() if k != 'tool'}
        payload = {"tool": tool_name, "params": params}
        timeout_default = 90 if tool_name == 'call_llm' else 60
        timeout = kwargs.get('timeout', timeout_default)
        
        # Transport retry (3×)
        result = self._call_with_transport_retry(payload, timeout, retries=3)
        
        # Build debug preview (10KB) but preserve original shape for outputs
        try:
            from ..engine.debug_utils import _preview
            preview = {
                "inputs": {"tool": tool_name, **({k: params[k] for k in ('model','temperature') if k in params})},
                "params": _preview(params),
                "messages": _preview(params.get('messages')) if 'messages' in params else None,
                "output": _preview(result),
            }
            if isinstance(result, dict):
                result["__debug_preview"] = preview
                return result
            else:
                # Promote scalar/str to dict with content key for mapping compatibility
                return {"content": result, "__debug_preview": preview}
        except Exception:
            # Fallback: return original result on any preview error
            return result
    
    def _call_with_transport_retry(self, payload: Dict, timeout: int, retries: int) -> Dict:
        for attempt in range(retries):
            try:
                response = requests.post(
                    self._endpoint,
                    json=payload,
                    timeout=timeout,
                    headers={"Content-Type": "application/json"}
                )
                return self._handle_response(response)
            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt == retries - 1:
                    raise HandlerError(
                        message=f"Transport failure after {retries} attempts: {str(e)[:200]}",
                        code="TRANSPORT_FAILURE",
                        category="io",
                        retryable=True
                    )
                time.sleep(0.5 * (2 ** attempt))
        raise HandlerError(
            message="Transport retry exhausted",
            code="TRANSPORT_FAILURE",
            category="io",
            retryable=True
        )
    
    def _handle_response(self, response) -> Dict:
        status = response.status_code
        if 200 <= status < 300:
            try:
                body = response.json()
            except json.JSONDecodeError:
                raise HandlerError(
                    message="Response body is not valid JSON",
                    code="INVALID_RESPONSE",
                    category="validation",
                    retryable=False
                )
            if isinstance(body, dict) and 'result' in body:
                return body['result']
            return body
        elif status == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise HandlerError(
                message=f"Rate limited, retry after {retry_after}s",
                code="RATE_LIMIT",
                category="io",
                retryable=True,
                details={"retry_after_sec": retry_after}
            )
        elif 400 <= status < 500:
            try:
                body = response.json()
                error_msg = body.get("error", {}).get("message", response.text[:200])
            except:
                error_msg = response.text[:200]
            raise HandlerError(
                message=f"Client error {status}: {error_msg}",
                code=f"HTTP_{status}",
                category="validation",
                retryable=False
            )
        elif 500 <= status < 600:
            try:
                body = response.json()
                error_msg = body.get("error", {}).get("message", response.text[:200])
            except:
                error_msg = response.text[:200]
            raise HandlerError(
                message=f"Server error {status}: {error_msg}",
                code=f"HTTP_{status}",
                category="io",
                retryable=True
            )
        else:
            raise HandlerError(
                message=f"Unexpected HTTP status {status}",
                code=f"HTTP_{status}",
                category="io",
                retryable=False
            )
