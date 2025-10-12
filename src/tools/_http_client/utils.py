"""Utility functions for HTTP Client."""
from __future__ import annotations
from typing import Dict, Any, Optional
import json
from pathlib import Path


def parse_response(
    response,
    response_format: str = "auto"
) -> Dict[str, Any]:
    """Parse HTTP response based on format.
    
    Args:
        response: requests.Response object
        response_format: Desired format (auto, json, text, raw)
        
    Returns:
        Dict with parsed response data
    """
    result = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "ok": response.ok
    }
    
    # Handle different response formats
    if response_format == "raw":
        result["body"] = response.content.decode("utf-8", errors="replace")
        result["body_length"] = len(response.content)
        return result
    
    content_type = response.headers.get("Content-Type", "").lower()
    
    # Auto-detect format
    if response_format == "auto":
        if "application/json" in content_type:
            response_format = "json"
        else:
            response_format = "text"
    
    # Parse based on format
    if response_format == "json":
        try:
            result["body"] = response.json()
        except json.JSONDecodeError as e:
            result["body"] = response.text
            result["json_error"] = f"Failed to parse JSON: {str(e)}"
    else:  # text
        result["body"] = response.text
    
    result["body_length"] = len(response.content)
    
    return result


def save_response_to_file(response_Dict[str, Any], filename: Optional[str] = None) -> Dict[str, Any]:
    """Save response to files/http_responses/.
    
    Args:
        response_data: Parsed response data
        filename: Optional custom filename
        
    Returns:
        Dict with save status and file path
    """
    try:
        # Project root
        project_root = Path(__file__).parent.parent.parent.parent
        save_dir = project_root / "files" / "http_responses"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            status = response_data.get("status_code", "unknown")
            filename = f"response_{timestamp}_{status}.json"
        
        # Ensure .json extension
        if not filename.endswith(".json"):
            filename += ".json"
        
        file_path = save_dir / filename
        
        # Save
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)
        
        return {
            "file_path": str(file_path),
            "filename": filename
        }
        
    except Exception as e:
        return {
            "error": f"Failed to save response: {str(e)}"
        }


def build_request_summary(method: str, url: str, **params) -> Dict[str, Any]:
    """Build a summary of the request for logging/debugging.
    
    Args:
        method: HTTP method
        url: Target URL
        **params: Request parameters
        
    Returns:
        Dict with request summary
    """
    summary = {
        "method": method,
        "url": url
    }
    
    if params.get("headers"):
        summary["headers"] = params["headers"]
    
    if params.get("params"):
        summary["query_params"] = params["params"]
    
    if params.get("json"):
        summary["body_type"] = "json"
    elif params.get("form_data"):
        summary["body_type"] = "form_data"
    elif params.get("body"):
        summary["body_type"] = "raw"
    
    if params.get("auth_type") and params["auth_type"] != "none":
        summary["auth"] = params["auth_type"]
    
    if params.get("timeout"):
        summary["timeout"] = params["timeout"]
    
    if params.get("max_retries", 0) > 0:
        summary["max_retries"] = params["max_retries"]
    
    return summary
