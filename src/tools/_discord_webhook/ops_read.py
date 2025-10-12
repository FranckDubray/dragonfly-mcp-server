from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import HTTPException

try:
    from .util import get_discord_webhook_url, parse_webhook, API_BASE
    from .http_client import http_request
    from . import db as DB
except Exception:
    from src.tools._discord_webhook.util import get_discord_webhook_url, parse_webhook, API_BASE
    from src.tools._discord_webhook.http_client import http_request
    from src.tools._discord_webhook import db as DB


def _safe_message_id(value: Any) -> str:
    """Safely convert any value to a Discord message ID string."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(int(value))
    return str(value)


def _parse_message(raw_msg: Dict[str, Any], include_metadata: bool, parse_embeds: bool) -> Dict[str, Any]:
    """Parse Discord message object into structured output."""
    msg: Dict[str, Any] = {
        "id": raw_msg.get("id"),
        "content": raw_msg.get("content"),
        "timestamp": raw_msg.get("timestamp"),
    }
    
    embeds_raw = raw_msg.get("embeds", [])
    if parse_embeds:
        msg["embeds"] = embeds_raw
        msg["embeds_count"] = len(embeds_raw)
    else:
        msg["embeds_count"] = len(embeds_raw)
        msg["embeds_raw"] = embeds_raw
    
    if include_metadata:
        reactions = raw_msg.get("reactions", [])
        if reactions:
            msg["reactions"] = [
                {"emoji": r.get("emoji", {}).get("name"), "count": r.get("count", 0), "me": r.get("me", False)}
                for r in reactions
            ]
        
        mentions_users = raw_msg.get("mentions", [])
        if mentions_users:
            msg["mentions_users"] = [
                {"id": u.get("id"), "username": u.get("username")} for u in mentions_users
            ]
        
        mention_roles = raw_msg.get("mention_roles", [])
        if mention_roles:
            msg["mention_roles"] = mention_roles
        
        if raw_msg.get("mention_everyone", False):
            msg["mention_everyone"] = True
        
        attachments = raw_msg.get("attachments", [])
        if attachments:
            msg["attachments"] = [
                {"id": a.get("id"), "filename": a.get("filename"), "size": a.get("size"), "url": a.get("url"), "content_type": a.get("content_type")}
                for a in attachments
            ]
        
        msg["edited_timestamp"] = raw_msg.get("edited_timestamp")
        msg["pinned"] = raw_msg.get("pinned", False)
        msg["tts"] = raw_msg.get("tts", False)
        msg["type"] = raw_msg.get("type")
        msg["webhook_id"] = raw_msg.get("webhook_id")
        msg["channel_id"] = raw_msg.get("channel_id")
    
    return msg


def _read_single_message(wh_id: str, token: str, message_id: str, thread_id: Optional[str], include_metadata: bool, parse_embeds: bool) -> Dict[str, Any]:
    """Read a single Discord message via webhook API."""
    url = f"{API_BASE}/webhooks/{wh_id}/{token}/messages/{message_id}"
    if thread_id:
        url += f"?thread_id={thread_id}"
    
    res = http_request("GET", url, allow_429_retry=True)
    
    if res.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
    if res.status_code >= 300:
        raise HTTPException(status_code=502, detail=f"Discord GET failed (status {res.status_code})")
    
    if not res.json:
        raise HTTPException(status_code=502, detail="Discord returned empty response")
    
    return _parse_message(res.json, include_metadata, parse_embeds)


def op_read(params: Dict[str, Any]) -> Dict[str, Any]:
    """Read operation: fetch Discord message(s) via webhook API."""
    url = get_discord_webhook_url()
    wh_id, token = parse_webhook(url)
    
    message_id_raw = params.get("message_id")
    message_id = _safe_message_id(message_id_raw) if message_id_raw else None
    
    message_ids_raw = params.get("message_ids") or []
    message_ids = [_safe_message_id(mid) for mid in message_ids_raw] if message_ids_raw else []
    
    article_key = params.get("article_key")
    
    thread_id_raw = params.get("thread_id")
    thread_id = _safe_message_id(thread_id_raw) if thread_id_raw else None
    
    include_metadata = params.get("include_metadata", True)
    parse_embeds = params.get("parse_embeds", True)
    
    if not message_id and not message_ids and not article_key:
        raise HTTPException(status_code=400, detail="read: message_id, message_ids, or article_key required")
    
    if message_ids and len(message_ids) > 50:
        raise HTTPException(status_code=400, detail="read: message_ids max 50 items")
    
    messages_to_read: List[str] = []
    
    if message_id:
        messages_to_read.append(message_id)
    elif message_ids:
        messages_to_read.extend(message_ids)
    elif article_key:
        with DB.db_conn() as conn:
            row = DB.db_get(conn, article_key)
            if not row:
                raise HTTPException(status_code=404, detail=f"read: article_key '{article_key}' not found in store")
            stored_ids = row.get("message_ids") or []
            if not stored_ids:
                return {"status": "ok", "operation": "read", "article_key": article_key, "messages": [], "count": 0, "note": "No messages stored for this article_key"}
            messages_to_read.extend([_safe_message_id(mid) for mid in stored_ids])
    
    fetched: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    
    for mid in messages_to_read:
        try:
            msg = _read_single_message(wh_id, token, mid, thread_id, include_metadata, parse_embeds)
            fetched.append(msg)
        except HTTPException as e:
            errors.append({"message_id": mid, "error": e.detail, "status_code": e.status_code})
        except Exception as e:
            errors.append({"message_id": mid, "error": str(e), "status_code": 500})
    
    result: Dict[str, Any] = {"status": "ok", "operation": "read", "messages": fetched, "count": len(fetched)}
    
    if article_key:
        result["article_key"] = article_key
    
    if errors:
        result["errors"] = errors
        result["errors_count"] = len(errors)
    
    return result
