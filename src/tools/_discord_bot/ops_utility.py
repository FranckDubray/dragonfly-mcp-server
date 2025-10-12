"""
Discord Bot: Search & utility operations (8 ops - updated).
"""
from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime
from .client import http_request
from .utils import safe_snowflake, check_response, parse_iso_datetime

def op_list_guilds(params: Dict[str, Any]) -> Dict[str, Any]:
    """List all guilds (servers) where the bot is a member."""
    limit = min(int(params.get("limit", 100)), 200)
    endpoint = f"/users/@me/guilds?limit={limit}"
    result = http_request("GET", endpoint)
    check_response(result, "list_guilds")
    
    guilds = result.json or []
    
    return {
        "status": "ok",
        "operation": "list_guilds",
        "guilds": guilds,
        "count": len(guilds)
    }

def op_search_messages(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search messages in a channel (local filtering).
    Note: Discord doesn't have a public search endpoint, so we fetch and filter locally.
    """
    channel_id = safe_snowflake(params.get("channel_id"))
    search_query = params.get("search_query", "").lower()
    author_filter = params.get("author_filter")
    date_from = params.get("date_from")
    date_to = params.get("date_to")
    
    if not channel_id:
        return {"error": "channel_id required"}
    
    # Fetch messages (max 100)
    limit = min(int(params.get("limit", 50)), 100)
    endpoint = f"/channels/{channel_id}/messages?limit={limit}"
    result = http_request("GET", endpoint)
    check_response(result, "search_messages")
    
    messages = result.json or []
    
    # Filter locally
    filtered: List[Dict[str, Any]] = []
    
    for msg in messages:
        # Content search
        if search_query:
            content = (msg.get("content") or "").lower()
            if search_query not in content:
                continue
        
        # Author filter
        if author_filter:
            author = msg.get("author", {})
            author_id = author.get("id", "")
            author_username = (author.get("username") or "").lower()
            if author_filter not in [author_id, author_username]:
                continue
        
        # Date range filter
        if date_from or date_to:
            timestamp_str = msg.get("timestamp")
            if timestamp_str:
                msg_dt = parse_iso_datetime(timestamp_str)
                if msg_dt:
                    if date_from:
                        from_dt = parse_iso_datetime(date_from)
                        if from_dt and msg_dt < from_dt:
                            continue
                    if date_to:
                        to_dt = parse_iso_datetime(date_to)
                        if to_dt and msg_dt > to_dt:
                            continue
        
        filtered.append(msg)
    
    return {
        "status": "ok",
        "operation": "search_messages",
        "messages": filtered,
        "count": len(filtered),
        "total_scanned": len(messages)
    }

def op_get_guild_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get guild (server) information."""
    guild_id = safe_snowflake(params.get("guild_id"))
    if not guild_id:
        return {"error": "guild_id required"}
    
    endpoint = f"/guilds/{guild_id}"
    result = http_request("GET", endpoint)
    check_response(result, "get_guild_info")
    
    return {
        "status": "ok",
        "operation": "get_guild_info",
        "guild": result.json
    }

def op_list_members(params: Dict[str, Any]) -> Dict[str, Any]:
    """List guild members."""
    guild_id = safe_snowflake(params.get("guild_id"))
    if not guild_id:
        return {"error": "guild_id required"}
    
    limit = min(int(params.get("limit", 50)), 1000)
    endpoint = f"/guilds/{guild_id}/members?limit={limit}"
    result = http_request("GET", endpoint)
    check_response(result, "list_members")
    
    return {
        "status": "ok",
        "operation": "list_members",
        "members": result.json or [],
        "count": len(result.json or [])
    }

def op_get_permissions(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get bot's permissions in a channel."""
    channel_id = safe_snowflake(params.get("channel_id"))
    if not channel_id:
        return {"error": "channel_id required"}
    
    # Get channel info (includes permission_overwrites)
    endpoint = f"/channels/{channel_id}"
    result = http_request("GET", endpoint)
    check_response(result, "get_permissions")
    
    channel_data = result.json or {}
    
    return {
        "status": "ok",
        "operation": "get_permissions",
        "channel_id": channel_id,
        "permission_overwrites": channel_data.get("permission_overwrites", [])
    }

def op_get_user(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get user information."""
    user_id = safe_snowflake(params.get("user_id"))
    if not user_id:
        return {"error": "user_id required"}
    
    endpoint = f"/users/{user_id}"
    result = http_request("GET", endpoint)
    check_response(result, "get_user")
    
    return {
        "status": "ok",
        "operation": "get_user",
        "user": result.json
    }

def op_list_emojis(params: Dict[str, Any]) -> Dict[str, Any]:
    """List custom emojis in a guild."""
    guild_id = safe_snowflake(params.get("guild_id"))
    if not guild_id:
        return {"error": "guild_id required"}
    
    endpoint = f"/guilds/{guild_id}/emojis"
    result = http_request("GET", endpoint)
    check_response(result, "list_emojis")
    
    return {
        "status": "ok",
        "operation": "list_emojis",
        "emojis": result.json or [],
        "count": len(result.json or [])
    }

def op_health_check(params: Dict[str, Any]) -> Dict[str, Any]:
    """Test bot connection and token validity."""
    try:
        endpoint = "/users/@me"
        result = http_request("GET", endpoint, timeout=10.0)
        
        if result.status_code == 401:
            return {
                "status": "error",
                "operation": "health_check",
                "error": "Invalid bot token (401 Unauthorized)"
            }
        
        check_response(result, "health_check")
        
        bot_user = result.json or {}
        
        return {
            "status": "ok",
            "operation": "health_check",
            "bot_user": bot_user,
            "connection": "healthy"
        }
    except Exception as e:
        return {
            "status": "error",
            "operation": "health_check",
            "error": str(e)
        }
