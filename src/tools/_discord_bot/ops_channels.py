"""
Discord Bot: Channel operations (5 ops).
"""
from __future__ import annotations
from typing import Any, Dict
from .client import http_request
from .utils import safe_snowflake, check_response

def op_list_channels(params: Dict[str, Any]) -> Dict[str, Any]:
    """List all channels in a guild."""
    guild_id = safe_snowflake(params.get("guild_id"))
    if not guild_id:
        return {"error": "guild_id required"}
    
    endpoint = f"/guilds/{guild_id}/channels"
    result = http_request("GET", endpoint)
    check_response(result, "list_channels")
    
    return {
        "status": "ok",
        "operation": "list_channels",
        "channels": result.json or [],
        "count": len(result.json or [])
    }

def op_get_channel(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get channel details."""
    channel_id = safe_snowflake(params.get("channel_id"))
    if not channel_id:
        return {"error": "channel_id required"}
    
    endpoint = f"/channels/{channel_id}"
    result = http_request("GET", endpoint)
    check_response(result, "get_channel")
    
    return {
        "status": "ok",
        "operation": "get_channel",
        "channel": result.json
    }

def op_create_channel(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new channel."""
    guild_id = safe_snowflake(params.get("guild_id"))
    name = params.get("name")
    
    if not guild_id or not name:
        return {"error": "guild_id and name required"}
    
    payload: Dict[str, Any] = {"name": name[:100]}
    
    if params.get("type") is not None:
        payload["type"] = int(params["type"])
    
    if params.get("topic"):
        payload["topic"] = params["topic"][:1024]
    
    endpoint = f"/guilds/{guild_id}/channels"
    result = http_request("POST", endpoint, json_body=payload)
    check_response(result, "create_channel")
    
    return {
        "status": "ok",
        "operation": "create_channel",
        "channel": result.json
    }

def op_modify_channel(params: Dict[str, Any]) -> Dict[str, Any]:
    """Modify a channel."""
    channel_id = safe_snowflake(params.get("channel_id"))
    if not channel_id:
        return {"error": "channel_id required"}
    
    payload: Dict[str, Any] = {}
    
    if params.get("name"):
        payload["name"] = params["name"][:100]
    
    if params.get("topic") is not None:
        payload["topic"] = params["topic"][:1024]
    
    if not payload:
        return {"error": "name or topic required for modification"}
    
    endpoint = f"/channels/{channel_id}"
    result = http_request("PATCH", endpoint, json_body=payload)
    check_response(result, "modify_channel")
    
    return {
        "status": "ok",
        "operation": "modify_channel",
        "channel": result.json
    }

def op_delete_channel(params: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a channel."""
    channel_id = safe_snowflake(params.get("channel_id"))
    if not channel_id:
        return {"error": "channel_id required"}
    
    endpoint = f"/channels/{channel_id}"
    result = http_request("DELETE", endpoint)
    check_response(result, "delete_channel")
    
    return {
        "status": "ok",
        "operation": "delete_channel",
        "channel_id": channel_id
    }
