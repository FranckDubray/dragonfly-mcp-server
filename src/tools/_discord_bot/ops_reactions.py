"""
Discord Bot: Reaction operations (3 ops).
"""
from __future__ import annotations
from typing import Any, Dict
import urllib.parse
from .client import http_request
from .utils import safe_snowflake, check_response

def _encode_emoji(emoji: str) -> str:
    """URL-encode emoji for Discord API."""
    return urllib.parse.quote(emoji, safe='')

def op_add_reaction(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add a reaction to a message."""
    channel_id = safe_snowflake(params.get("channel_id"))
    message_id = safe_snowflake(params.get("message_id"))
    emoji = params.get("emoji")
    
    if not channel_id or not message_id or not emoji:
        return {"error": "channel_id, message_id, and emoji required"}
    
    emoji_encoded = _encode_emoji(emoji)
    endpoint = f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji_encoded}/@me"
    result = http_request("PUT", endpoint)
    check_response(result, "add_reaction")
    
    return {
        "status": "ok",
        "operation": "add_reaction",
        "emoji": emoji
    }

def op_remove_reaction(params: Dict[str, Any]) -> Dict[str, Any]:
    """Remove bot's reaction from a message."""
    channel_id = safe_snowflake(params.get("channel_id"))
    message_id = safe_snowflake(params.get("message_id"))
    emoji = params.get("emoji")
    
    if not channel_id or not message_id or not emoji:
        return {"error": "channel_id, message_id, and emoji required"}
    
    emoji_encoded = _encode_emoji(emoji)
    endpoint = f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji_encoded}/@me"
    result = http_request("DELETE", endpoint)
    check_response(result, "remove_reaction")
    
    return {
        "status": "ok",
        "operation": "remove_reaction",
        "emoji": emoji
    }

def op_get_reactions(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get users who reacted with a specific emoji."""
    channel_id = safe_snowflake(params.get("channel_id"))
    message_id = safe_snowflake(params.get("message_id"))
    emoji = params.get("emoji")
    
    if not channel_id or not message_id or not emoji:
        return {"error": "channel_id, message_id, and emoji required"}
    
    limit = min(int(params.get("limit", 50)), 100)
    emoji_encoded = _encode_emoji(emoji)
    endpoint = f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji_encoded}?limit={limit}"
    result = http_request("GET", endpoint)
    check_response(result, "get_reactions")
    
    return {
        "status": "ok",
        "operation": "get_reactions",
        "emoji": emoji,
        "users": result.json or [],
        "count": len(result.json or [])
    }
