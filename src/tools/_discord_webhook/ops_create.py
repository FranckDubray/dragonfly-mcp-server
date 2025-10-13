"""Create operation for discord_webhook."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import logging

try:
    from .util import get_discord_webhook_url
    from .http_client import http_request
    from . import db as DB
except Exception:
    from src.tools._discord_webhook.util import get_discord_webhook_url
    from src.tools._discord_webhook.http_client import http_request
    from src.tools._discord_webhook import db as DB

logger = logging.getLogger(__name__)


def _build_url_with_thread(base_url: str, thread_id: Optional[str]) -> str:
    """Append thread_id query param if provided."""
    if thread_id:
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}thread_id={thread_id}"
    return base_url


def op_create(
    article_key: str,
    batches: List[List[Dict[str, Any]]],
    counts: List[int],
    files_data,
    wait: bool,
    payload_builder,
    wh_hash: str,
    thread_id: Optional[str],
) -> Dict[str, Any]:
    """Execute create operation: post new article to Discord."""
    url = get_discord_webhook_url()
    url = _build_url_with_thread(url, thread_id)
    
    posted_batches = 0
    new_message_ids: List[str] = []

    logger.info(f"Creating article '{article_key}' with {len(batches)} batch(es), {sum(counts)} total embeds")

    if files_data:
        logger.info(f"Posting with {len(files_data)} attachment(s)")
        from .sender import send_create_batches
        posted_batches, new_message_ids = send_create_batches(
            url=url,
            batches=batches,
            wait=wait,
            build_payload_for_batch=payload_builder,
            files_data=files_data,
        )
    else:
        for i in range(len(batches)):
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
                logger.info(f"Posted batch {i+1}/{len(batches)}: message_id={msg_id}")

    with DB.db_conn() as conn:
        DB.db_create(conn, article_key, wh_hash, new_message_ids, counts)
    
    logger.info(f"Article '{article_key}' created successfully: {len(new_message_ids)} message(s)")

    base: Dict[str, Any] = {
        "status": "ok",
        "operation": "create",
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
            {"id": mid, "embeds_count": counts[i], "batch_index": i} for i, mid in enumerate(new_message_ids)
        ]
    return base
