"""Update operation for discord_webhook."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import logging

try:
    from .util import get_discord_webhook_url, API_BASE
    from .http_client import http_request
    from . import db as DB
except Exception:
    from src.tools._discord_webhook.util import get_discord_webhook_url, API_BASE
    from src.tools._discord_webhook.http_client import http_request
    from src.tools._discord_webhook import db as DB

logger = logging.getLogger(__name__)


def _build_url_with_thread(base_url: str, thread_id: Optional[str]) -> str:
    """Append thread_id query param if provided."""
    if thread_id:
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}thread_id={thread_id}"
    return base_url


def op_update(
    article_key: str,
    batches: List[List[Dict[str, Any]]],
    counts: List[int],
    files_data,
    wait: bool,
    payload_builder,
    wh_id: str,
    token: str,
    existing_ids: List[str],
    wh_hash: str,
    thread_id: Optional[str],
) -> Dict[str, Any]:
    """Execute update operation: edit existing article on Discord."""
    posted_batches = 0
    new_message_ids: List[str] = []

    logger.info(f"Updating article '{article_key}': {len(existing_ids)} existing → {len(batches)} new batch(es)")

    if not wait and len(batches) != len(existing_ids):
        logger.error("Update with wait=false requires batch count to remain unchanged")
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="update avec wait=false requiert que le nombre de messages ne change pas (sinon impossible de maintenir l'état)")

    url = get_discord_webhook_url()
    url = _build_url_with_thread(url, thread_id)

    if files_data:
        logger.info(f"Updating with {len(files_data)} attachment(s)")
        from .sender import send_update_batches
        posted_batches, maybe_new_ids = send_update_batches(
            wh_id=wh_id,
            token=token,
            url=url,
            messages_ids_existing=existing_ids,
            batches=batches,
            wait=wait,
            build_payload_for_batch=payload_builder,
            files_data=files_data,
        )
        new_message_ids = maybe_new_ids or existing_ids
    else:
        min_len = min(len(existing_ids), len(batches))
        for i in range(min_len):
            msg_id = existing_ids[i]
            payload = payload_builder(i)
            res = http_request("PATCH", f"{API_BASE}/webhooks/{wh_id}/{token}/messages/{msg_id}", json_body=payload)
            posted_batches += 1
            if res.status_code >= 300:
                logger.error(f"Discord PATCH failed for message {msg_id}: status {res.status_code}")
                from fastapi import HTTPException
                raise HTTPException(status_code=502, detail=f"Discord PATCH a échoué (statut {res.status_code}).")
            new_message_ids.append(msg_id)
            logger.info(f"Updated batch {i+1}/{min_len}: message_id={msg_id}")
        
        if len(batches) > len(existing_ids):
            logger.info(f"Adding {len(batches) - len(existing_ids)} new message(s)")
            for i in range(len(existing_ids), len(batches)):
                payload = payload_builder(i)
                res = http_request("POST", f"{url}?wait={'true' if wait else 'false'}", json_body=payload)
                posted_batches += 1
                if wait:
                    if res.status_code >= 300 or not res.json:
                        logger.error(f"Discord POST failed: status {res.status_code}")
                        from fastapi import HTTPException
                        raise HTTPException(status_code=502, detail=f"Discord POST a échoué (statut {res.status_code}).")
                    msg_id = str(res.json.get("id")) if res.json else None
                    if not msg_id:
                        logger.error("Discord did not return message id")
                        from fastapi import HTTPException
                        raise HTTPException(status_code=502, detail="Discord n'a pas renvoyé d'id de message.")
                    new_message_ids.append(msg_id)
                    logger.info(f"Added batch {i+1}/{len(batches)}: message_id={msg_id}")
        
        elif len(batches) < len(existing_ids):
            deleted_count = len(existing_ids) - len(batches)
            logger.warning(f"Deleting {deleted_count} extra message(s)")
            for i in range(len(existing_ids) - 1, len(batches) - 1, -1):
                msg_id = existing_ids[i]
                res = http_request("DELETE", f"{API_BASE}/webhooks/{wh_id}/{token}/messages/{msg_id}")
                posted_batches += 1
                if not (200 <= res.status_code < 300 or res.status_code == 404):
                    logger.error(f"Discord DELETE failed for message {msg_id}: status {res.status_code}")
                    from fastapi import HTTPException
                    raise HTTPException(status_code=502, detail=f"Discord DELETE a échoué (statut {res.status_code}).")
                logger.info(f"Deleted extra message: {msg_id}")

    # Persist mapping
    try:
        with DB.db_conn() as conn:
            if len(new_message_ids) < len(batches):
                new_message_ids = existing_ids[:len(batches)]
            DB.db_update(conn, article_key, wh_hash, new_message_ids or existing_ids, counts)
    except Exception as e:
        if "missing" in str(e).lower():
            logger.warning(f"Article '{article_key}' not found in DB, creating new entry")
            with DB.db_conn() as conn:
                DB.db_create(conn, article_key, wh_hash, new_message_ids or existing_ids, counts)
        else:
            raise

    logger.info(f"Article '{article_key}' updated successfully: {len(new_message_ids or existing_ids)} message(s)")

    base: Dict[str, Any] = {
        "status": "ok",
        "operation": "update",
        "posted_batches": posted_batches,
        "total_embeds": sum(counts),
        "split_applied": sum(counts) > 1,
        "article_key": article_key,
    }
    
    if sum(counts) > 1:
        logger.warning(f"Article '{article_key}' was split into {len(batches)} message(s) (total embeds: {sum(counts)})")
        base["note"] = f"Content was split into {len(batches)} message(s) due to Discord embed limits"
    
    if wait:
        base["messages"] = [
            {"id": mid, "embeds_count": counts[i], "batch_index": i}
            for i, mid in enumerate(new_message_ids or existing_ids)
        ]
    return base
