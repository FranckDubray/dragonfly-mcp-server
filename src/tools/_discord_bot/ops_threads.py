"""
Discord Bot: Thread operations (5 ops).
"""
from __future__ import annotations
from typing import Any, Dict
from .client import http_request
from .utils import safe_snowflake, check_response

def op_create_thread(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new thread."""
    channel_id = safe_snowflake(params.get("channel_id"))
    name = params.get("name")
    
    if not channel_id or not name:
        return {"error": "channel_id and name required"}
    
    payload: Dict[str, Any] = {"name": name[:100]}
    
    # Auto archive duration (minutes)
    if params.get("auto_archive_duration"):
        payload["auto_archive_duration"] = int(params["auto_archive_duration"])
    
    # Thread type (10=announcement, 11=public, 12=private)
    if params.get("type"):
        payload["type"] = int(params["type"])
    
    endpoint = f"/channels/{channel_id}/threads"
    result = http_request("POST", endpoint, json_body=payload)
    check_response(result, "create_thread")
    
    return {
        "status": "ok",
        "operation": "create_thread",
        "thread": result.json
    }

def op_list_threads(params: Dict[str, Any]) -> Dict[str, Any]:
    """List active threads in a channel."""
    channel_id = safe_snowflake(params.get("channel_id"))
    if not channel_id:
        return {"error": "channel_id required"}
    
    endpoint = f"/channels/{channel_id}/threads/active"
    result = http_request("GET", endpoint)
    check_response(result, "list_threads")
    
    threads = []
    if result.json and isinstance(result.json, dict):
        threads = result.json.get("threads", [])
    
    return {
        "status": "ok",
        "operation": "list_threads",
        "threads": threads,
        "count": len(threads)
    }

def op_join_thread(params: Dict[str, Any]) -> Dict[str, Any]:
    """Join a thread."""
    thread_id = safe_snowflake(params.get("thread_id"))
    if not thread_id:
        return {"error": "thread_id required"}
    
    endpoint = f"/channels/{thread_id}/thread-members/@me"
    result = http_request("PUT", endpoint)
    check_response(result, "join_thread")
    
    return {
        "status": "ok",
        "operation": "join_thread",
        "thread_id": thread_id
    }

def op_leave_thread(params: Dict[str, Any]) -> Dict[str, Any]:
    """Leave a thread."""
    thread_id = safe_snowflake(params.get("thread_id"))
    if not thread_id:
        return {"error": "thread_id required"}
    
    endpoint = f"/channels/{thread_id}/thread-members/@me"
    result = http_request("DELETE", endpoint)
    check_response(result, "leave_thread")
    
    return {
        "status": "ok",
        "operation": "leave_thread",
        "thread_id": thread_id
    }

def op_archive_thread(params: Dict[str, Any]) -> Dict[str, Any]:
    """Archive a thread."""
    thread_id = safe_snowflake(params.get("thread_id"))
    if not thread_id:
        return {"error": "thread_id required"}
    
    payload = {"archived": True}
    endpoint = f"/channels/{thread_id}"
    result = http_request("PATCH", endpoint, json_body=payload)
    check_response(result, "archive_thread")
    
    return {
        "status": "ok",
        "operation": "archive_thread",
        "thread_id": thread_id
    }
