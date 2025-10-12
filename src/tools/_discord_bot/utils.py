"""
Utility functions for discord_bot.
"""
from __future__ import annotations
from typing import Any, Optional, Dict, List
from datetime import datetime

def safe_snowflake(value: Any) -> str:
    """Safely convert any value to a Discord snowflake string."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value))
    return str(value)

def parse_iso_datetime(dt_str: str) -> Optional[datetime]:
    """Parse ISO 8601 datetime string."""
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except Exception:
        return None

def check_response(result, operation: str):
    """Check HTTP result and raise on error."""
    if result.status_code == 401:
        raise ValueError(f"{operation}: Invalid bot token (401 Unauthorized)")
    if result.status_code == 403:
        raise ValueError(f"{operation}: Missing permissions (403 Forbidden)")
    if result.status_code == 404:
        raise ValueError(f"{operation}: Resource not found (404)")
    if result.status_code >= 400:
        error_msg = "Unknown error"
        if result.json and isinstance(result.json, dict):
            error_msg = result.json.get("message", error_msg)
        raise RuntimeError(f"{operation}: Discord API error ({result.status_code}): {error_msg}")

def _remove_null_fields(obj: Any) -> Any:
    """Recursively remove all null/empty/useless fields."""
    if isinstance(obj, dict):
        cleaned = {}
        for key, value in obj.items():
            # Skip null values
            if value is None:
                continue
            # Skip empty strings (but keep "0" discriminator)
            if isinstance(value, str) and value == "" and key != "discriminator":
                continue
            # Skip empty arrays
            if isinstance(value, list) and len(value) == 0:
                continue
            # Skip useless Discord metadata fields
            if key in ("public_flags", "flags", "banner", "accent_color", "avatar_decoration_data", 
                      "collectibles", "display_name_styles", "banner_color", "clan", "primary_guild",
                      "components", "mention_everyone", "pinned", "tts", "content_scan_version", 
                      "placeholder", "placeholder_version", "original_content_type", "title",
                      "proxy_url", "guild_id", "type", "channel_id", "me_burst", "burst_me", 
                      "me", "burst_count", "burst_colors", "count_details", "rate_limit_per_user",
                      "bitrate", "user_limit", "rtc_region", "owner_id", "thread_metadata"):
                continue
            # Recursively clean nested objects
            cleaned[key] = _remove_null_fields(value)
        return cleaned
    elif isinstance(obj, list):
        return [_remove_null_fields(item) for item in obj]
    else:
        return obj

def clean_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Remove null/useless fields from user object."""
    if not isinstance(user, dict):
        return user
    
    cleaned = {
        "id": user.get("id"),
        "username": user.get("username"),
    }
    
    # Only include non-null optional fields
    if user.get("global_name"):
        cleaned["global_name"] = user["global_name"]
    if user.get("avatar"):
        cleaned["avatar"] = user["avatar"]
    if user.get("bot"):
        cleaned["bot"] = True
    if user.get("discriminator") != "0":
        cleaned["discriminator"] = user["discriminator"]
    
    return _remove_null_fields(cleaned)

def clean_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Remove null/useless fields from message object - AGGRESSIVE CLEANING."""
    if not isinstance(msg, dict):
        return msg
    
    cleaned = {
        "id": msg.get("id"),
        "author": clean_user(msg.get("author", {})),
        "content": msg.get("content", ""),
        "timestamp": msg.get("timestamp"),
    }
    
    # Only include non-empty optional fields
    if msg.get("edited_timestamp"):
        cleaned["edited_timestamp"] = msg["edited_timestamp"]
    
    if msg.get("embeds") and len(msg["embeds"]) > 0:
        cleaned["embeds"] = msg["embeds"]
    
    if msg.get("attachments") and len(msg["attachments"]) > 0:
        # Clean attachments - ONLY essentials
        cleaned["attachments"] = [
            {k: v for k, v in {
                "filename": a.get("filename"),
                "size": a.get("size"),
                "url": a.get("url"),
                "content_type": a.get("content_type"),
                "width": a.get("width"),
                "height": a.get("height"),
            }.items() if v is not None}
            for a in msg["attachments"]
            if isinstance(a, dict)
        ]
    
    if msg.get("mentions") and len(msg["mentions"]) > 0:
        cleaned["mentions"] = [clean_user(u) for u in msg["mentions"]]
    
    if msg.get("mention_roles") and len(msg["mention_roles"]) > 0:
        cleaned["mention_roles"] = msg["mention_roles"]
    
    if msg.get("reactions") and len(msg["reactions"]) > 0:
        cleaned["reactions"] = [
            {"emoji": r.get("emoji", {}).get("name"), "count": r.get("count", 0)}
            for r in msg["reactions"]
            if isinstance(r, dict) and r.get("emoji", {}).get("name")
        ]
    
    # Referenced message (replies) - RECURSIVE with same cleaning
    if msg.get("message_reference"):
        ref = {"message_id": msg["message_reference"].get("message_id")}
        if msg.get("referenced_message"):
            ref["referenced_message"] = clean_message(msg["referenced_message"])
        cleaned["message_reference"] = ref
    
    # Thread info - MINIMAL
    if msg.get("thread"):
        cleaned["thread"] = {
            "id": msg["thread"].get("id"),
            "name": msg["thread"].get("name"),
            "message_count": msg["thread"].get("message_count"),
        }
    
    return _remove_null_fields(cleaned)

def clean_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean a list of messages."""
    return [clean_message(msg) for msg in messages if isinstance(msg, dict)]
