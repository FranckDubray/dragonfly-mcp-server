


# Generic MCP HTTP tool handler (POST /execute with 3-level retry)

import time
import json
from typing import Dict, Any
import sys

# Try to import requests, capture import error for diagnostics
try:
    import requests  # type: ignore
    _requests_import_error = None
except Exception as e:  # broader than ImportError for env issues
    requests = None  # type: ignore
    _requests_import_error = str(e)

# Fallback imports
import urllib.request
import urllib.error
import socket

from .base import AbstractHandler, HandlerError

class HttpToolHandler(AbstractHandler):
    """Generic HTTP tool handler (calls MCP server /execute endpoint) with urllib fallback if 'requests' is unavailable.

    Extra (generic) validation:
    - optional input `require_keys`: list[str] of keys that MUST be present in the returned result dict; otherwise raises HandlerError("MISSING_KEYS").
      This allows workflows to fail early at the IO node when a tool returns a structurally incomplete payload (e.g., call_llm without 'content').
    """
    
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
        tool_name = kwargs.get('tool')
        if not tool_name:
            raise HandlerError(
                message="Missing required parameter: tool",
                code="INVALID_INPUT",
                category="validation",
                retryable=False
            )
        
        # Extract local-only controls (not forwarded)
        require_keys = kwargs.get('require_keys')
        if require_keys is not None and not isinstance(require_keys, list):
            raise HandlerError(
                message="require_keys must be a list of strings",
                code="INVALID_INPUT",
                category="validation",
                retryable=False
            )
        
        # Build payload for remote tool call (strip local-only keys)
        forward_exclude = { 'tool', 'require_keys' }
        params = {k: v for k, v in kwargs.items() if k not in forward_exclude}
        payload = {"tool": tool_name, "params": params}
        timeout_default = 90 if tool_name == 'call_llm' else 60
        timeout = kwargs.get('timeout', timeout_default)
        
        # Transport retry (3×)
        result = self._call_with_transport_retry(payload, timeout, retries=3)
        
        # Optional structural validation: ensure required keys exist in result dict
        if isinstance(require_keys, list):
            if not isinstance(result, dict):
                raise HandlerError(
                    message="Result is not an object while require_keys was provided",
                    code="MISSING_KEYS",
                    category="validation",
                    retryable=False
                )
            for key in require_keys:
                if key not in result:
                    raise HandlerError(
                        message=f"Missing required key in result: '{key}'",
                        code="MISSING_KEYS",
                        category="validation",
                        retryable=False
                    )
        
        # Build debug preview (10KB) but preserve original shape for outputs
        try:
            from ..engine.debug_utils import _preview
            preview = {
                "inputs": {"tool": tool_name, **({k: params[k] for k in ('model','temperature') if k in params})},
                "params": _preview(params),
                "messages": _preview(params.get('messages')) if 'messages' in params else None,
                "output": _preview(result),
                "require_keys": require_keys or []
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
                if requests is not None:
                    response = requests.post(
                        self._endpoint,
                        json=payload,
                        timeout=timeout,
                        headers={"Content-Type": "application/json", "User-Agent": "Orchestrator/1.0"}
                    )
                    return self._handle_response(response.status_code, response.headers, response.text)
                else:
                    # urllib fallback
                    data = json.dumps(payload).encode('utf-8')
                    req = urllib.request.Request(
                        self._endpoint,
                        data=data,
                        headers={"Content-Type": "application/json", "User-Agent": "Orchestrator/1.0"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=timeout) as resp:
                        status = resp.getcode()
                        headers = dict(resp.headers.items()) if hasattr(resp, 'headers') else {}
                        body_text = resp.read().decode('utf-8', errors='replace')
                        return self._handle_response(status, headers, body_text)
            except (socket.timeout) as e:
                if attempt == retries - 1:
                    raise HandlerError(
                        message=f"Timeout after {retries} attempts: {str(e)[:200]}",
                        code="TIMEOUT",
                        category="timeout",
                        retryable=True
                    )
                time.sleep(0.5 * (2 ** (attempt)))
            except (urllib.error.URLError) as e:
                if attempt == retries - 1:
                    raise HandlerError(
                        message=f"Transport failure after {retries} attempts (urllib): {str(e)[:200]}",
                        code="TRANSPORT_FAILURE",
                        category="io",
                        retryable=True,
                        details={"import_error": _requests_import_error, "python": sys.executable}
                    )
                time.sleep(0.5 * (2 ** (attempt)))
            except Exception as e:
                # requests path or unexpected
                if attempt == retries - 1:
                    # If specifically requests missing, surface clearer message once
                    if requests is None and _requests_import_error:
                        raise HandlerError(
                            message=f"requests not available: {_requests_import_error} (python={sys.executable})",
                            code="MISSING_DEPENDENCY",
                            category="validation",
                            retryable=False
                        )
                    raise HandlerError(
                        message=f"HTTP call failed: {str(e)[:200]}",
                        code="HTTP_ERROR",
                        category="io",
                        retryable=True
                    )
                time.sleep(0.5 * (2 ** (attempt)))
        # Safety net
        raise HandlerError(
            message="Transport retry exhausted",
            code="TRANSPORT_FAILURE",
            category="io",
            retryable=True
        )
    
    def _handle_response(self, status: int, headers: Dict[str, Any], body_text: str) -> Dict:
        if 200 <= status < 300:
            try:
                body = json.loads(body_text)
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
            retry_after = int(headers.get("Retry-After", 60)) if headers else 60
            raise HandlerError(
                message=f"Rate limited, retry after {retry_after}s",
                code="RATE_LIMIT",
                category="io",
                retryable=True,
                details={"retry_after_sec": retry_after}
            )
        elif 400 <= status < 500:
            error_msg = body_text[:200]
            try:
                body = json.loads(body_text)
                if isinstance(body, dict):
                    # Prefer API error message when present
                    error_msg = body.get("error", {}).get("message", body.get("message", error_msg))
            except Exception:
                pass
            raise HandlerError(
                message=f"Client error {status}: {error_msg}",
                code=f"HTTP_{status}",
                category="validation",
                retryable=False
            )
        elif 500 <= status < 600:
            error_msg = body_text[:200]
            try:
                body = json.loads(body_text)
                if isinstance(body, dict):
                    error_msg = body.get("error", {}).get("message", body.get("message", error_msg))
            except Exception:
                pass
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
