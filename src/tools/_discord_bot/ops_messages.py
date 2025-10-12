"""
Discord Bot: Message operations (8 ops).
"""
from __future__ import annotations
from typing import Any, Dict
from .client import http_request
from .utils import safe_snowflake, check_response, clean_messages

def op_list_messages(params: Dict[str, Any]) -> Dict[str, Any]:
    """List messages in a channel."""
    channel_id = safe_snowflake(params.get("channel_id"))
    if not channel_id:
        return {"error": "channel_id required"}
    
    # LIMIT TO 5 by default, MAX 50 to avoid LLM flood
    limit = min(int(params.get("limit", 5)), 50)
    
    # Pagination support
    query_params = [f"limit={limit}"]
    
    if params.get("before"):
        query_params.append(f"before={safe_snowflake(params['before'])}")
    if params.get("after"):
        query_params.append(f"after={safe_snowflake(params['after'])}")
    if params.get("around"):
        query_params.append(f"around={safe_snowflake(params['around'])}")
    
    query_str = "&".join(query_params)
    endpoint = f"/channels/{channel_id}/messages?{query_str}"
    
    result = http_request("GET", endpoint)
    check_response(result, "list_messages")
    
    # Clean messages to remove null/useless fields
    cleaned = clean_messages(result.json or [])
    
    return {
        "status": "ok",
        "operation": "list_messages",
        "messages": cleaned,
        "count": len(cleaned)
    }

def op_get_message(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get a specific message."""
    channel_id = safe_snowflake(params.get("channel_id"))
    message_id = safe_snowflake(params.get("message_id"))
    
    if not channel_id or not message_id:
        return {"error": "channel_id and message_id required"}
    
    endpoint = f"/channels/{channel_id}/messages/{message_id}"
    result = http_request("GET", endpoint)
    check_response(result, "get_message")
    
    from .utils import clean_message
    
    return {
        "status": "ok",
        "operation": "get_message",
        "message": clean_message(result.json)
    }

def op_send_message(params: Dict[str, Any]) -> Dict[str, Any]:
    """Send a message to a channel."""
    channel_id = safe_snowflake(params.get("channel_id"))
    content = params.get("content")
    
    if not channel_id:
        return {"error": "channel_id required"}
    
    if not content and not params.get("embeds"):
        return {"error": "content or embeds required"}
    
    payload: Dict[str, Any] = {}
    if content:
        payload["content"] = str(content)[:2000]
    
    if params.get("embeds"):
        payload["embeds"] = params["embeds"]
    
    endpoint = f"/channels/{channel_id}/messages"
    result = http_request("POST", endpoint, json_body=payload)
    check_response(result, "send_message")
    
    from .utils import clean_message
    
    return {
        "status": "ok",
        "operation": "send_message",
        "message": clean_message(result.json)
    }

def op_edit_message(params: Dict[str, Any]) -> Dict[str, Any]:
    """Edit a message."""
    channel_id = safe_snowflake(params.get("channel_id"))
    message_id = safe_snowflake(params.get("message_id"))
    content = params.get("content")
    
    if not channel_id or not message_id:
        return {"error": "channel_id and message_id required"}
    
    payload: Dict[str, Any] = {}
    if content is not None:
        payload["content"] = str(content)[:2000]
    
    if params.get("embeds"):
        payload["embeds"] = params["embeds"]
    
    if not payload:
        return {"error": "content or embeds required"}
    
    endpoint = f"/channels/{channel_id}/messages/{message_id}"
    result = http_request("PATCH", endpoint, json_body=payload)
    check_response(result, "edit_message")
    
    from .utils import clean_message
    
    return {
        "status": "ok",
        "operation": "edit_message",
        "message": clean_message(result.json)
    }

def op_delete_message(params: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a message."""
    channel_id = safe_snowflake(params.get("channel_id"))
    message_id = safe_snowflake(params.get("message_id"))
    
    if not channel_id or not message_id:
        return {"error": "channel_id and message_id required"}
    
    endpoint = f"/channels/{channel_id}/messages/{message_id}"
    result = http_request("DELETE", endpoint)
    check_response(result, "delete_message")
    
    return {
        "status": "ok",
        "operation": "delete_message",
        "message_id": message_id
    }

def op_bulk_delete(params: Dict[str, Any]) -> Dict[str, Any]:
    """Bulk delete messages (2-100 messages, must be < 14 days old)."""
    channel_id = safe_snowflake(params.get("channel_id"))
    message_ids = params.get("message_ids", [])
    
    if not channel_id:
        return {"error": "channel_id required"}
    
    if not isinstance(message_ids, list) or len(message_ids) < 2 or len(message_ids) > 100:
        return {"error": "message_ids must be an array of 2-100 message IDs"}
    
    # Convert to strings
    message_ids = [safe_snowflake(mid) for mid in message_ids]
    
    payload = {"messages": message_ids}
    endpoint = f"/channels/{channel_id}/messages/bulk-delete"
    result = http_request("POST", endpoint, json_body=payload)
    check_response(result, "bulk_delete")
    
    return {
        "status": "ok",
        "operation": "bulk_delete",
        "deleted_count": len(message_ids)
    }

def op_pin_message(params: Dict[str, Any]) -> Dict[str, Any]:
    """Pin a message."""
    channel_id = safe_snowflake(params.get("channel_id"))
    message_id = safe_snowflake(params.get("message_id"))
    
    if not channel_id or not message_id:
        return {"error": "channel_id and message_id required"}
    
    endpoint = f"/channels/{channel_id}/pins/{message_id}"
    result = http_request("PUT", endpoint)
    check_response(result, "pin_message")
    
    return {
        "status": "ok",
        "operation": "pin_message",
        "message_id": message_id
    }

def op_unpin_message(params: Dict[str, Any]) -> Dict[str, Any]:
    """Unpin a message."""
    channel_id = safe_snowflake(params.get("channel_id"))
    message_id = safe_snowflake(params.get("message_id"))
    
    if not channel_id or not message_id:
        return {"error": "channel_id and message_id required"}
    
    endpoint = f"/channels/{channel_id}/pins/{message_id}"
    result = http_request("DELETE", endpoint)
    check_response(result, "unpin_message")
    
    return {
        "status": "ok",
        "operation": "unpin_message",
        "message_id": message_id
    }
