from typing import Any, Dict
import json
import os
import urllib.request
import urllib.error


class HttpToolHandler:
    """Autonomous HTTP tool invoker for the Python Orchestrator.
    - Calls the MCP server /execute endpoint (same machine) via HTTP.
    - No external dependencies; uses urllib from stdlib.
    - Base URL configurable via env MCP_SERVER_URL (default: http://127.0.0.1:8000).
    """

    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
        self.base_url = (base_url or os.getenv("MCP_SERVER_URL") or "http://127.0.0.1:8000").rstrip("/")
        self.timeout = float(timeout)

    def run(self, **kwargs) -> Dict[str, Any]:
        tool = kwargs.pop("tool", None)
        if not tool:
            raise ValueError("HttpToolHandler.run requires 'tool' in kwargs")
        payload = {"tool": tool, "params": kwargs}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=f"{self.base_url}/execute",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                try:
                    obj = json.loads(raw.decode("utf-8"))
                except Exception:
                    # Return a minimal envelope if server didn't return JSON
                    return {"accepted": False, "status": "error", "message": "Invalid JSON response from /execute", "raw": raw[:200].decode("utf-8", "ignore")}
                return obj
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "ignore") if hasattr(e, "read") else str(e)
            return {"accepted": False, "status": "error", "message": f"HTTP {e.code} calling /execute", "details": msg[:400]}
        except urllib.error.URLError as e:
            return {"accepted": False, "status": "error", "message": f"URLError calling /execute: {e.reason}", "details": str(e)[:400]}
        except Exception as e:
            return {"accepted": False, "status": "error", "message": f"Unexpected error calling /execute: {str(e)[:200]}"}
