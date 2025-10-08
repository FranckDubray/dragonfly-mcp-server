from __future__ import annotations
from typing import Any, Dict
from fastapi import HTTPException

try:
    from .ops_create_update import op_create_or_update  # type: ignore
    from .util import API_BASE, get_discord_webhook_url, parse_webhook, webhook_hash  # type: ignore
    from . import db as DB  # type: ignore
    from .http_client import http_request  # type: ignore
except Exception:
    from src.tools._discord_webhook.ops_create_update import op_create_or_update  # type: ignore
    from src.tools._discord_webhook.util import API_BASE, get_discord_webhook_url, parse_webhook, webhook_hash  # type: ignore
    from src.tools._discord_webhook import db as DB  # type: ignore
    from src.tools._discord_webhook.http_client import http_request  # type: ignore


def _op_delete(params: Dict[str, Any]) -> Dict[str, Any]:
    article_key = params.get("article_key")
    target_message_ids = params.get("target_message_ids") or []

    url = get_discord_webhook_url()
    wh_id, token = parse_webhook(url)
    wh_hash = webhook_hash(wh_id, token)

    to_delete = []
    with DB.db_conn() as conn:
        if article_key:
            row = DB.db_get(conn, article_key)
            if not row:
                return {"status": "ok", "operation": "delete", "deleted": 0, "article_key": article_key}
            if row.get("webhook_hash") != wh_hash:
                raise HTTPException(status_code=409, detail="Le webhook courant diffère de celui utilisé pour publier cet article. Les messages ne peuvent pas être supprimés après rotation du webhook.")
            to_delete = list(row.get("message_ids") or [])
        elif target_message_ids:
            to_delete = list(map(str, target_message_ids))
        else:
            raise HTTPException(status_code=400, detail="delete: article_key OU target_message_ids requis")

    deleted = 0
    for msg_id in to_delete:
        res = http_request("DELETE", f"{API_BASE}/webhooks/{wh_id}/{token}/messages/{msg_id}")
        if 200 <= res.status_code < 300 or res.status_code == 404:
            deleted += 1
        else:
            raise HTTPException(status_code=502, detail=f"Discord DELETE a échoué (statut {res.status_code}).")

    if article_key:
        with DB.db_conn() as conn:
            DB.db_delete(conn, article_key)

    return {"status": "ok", "operation": "delete", "deleted": deleted, "article_key": article_key}


def _op_get(params: Dict[str, Any]) -> Dict[str, Any]:
    article_key = params.get("article_key")
    if not article_key:
        raise HTTPException(status_code=400, detail="get: article_key requis")
    with DB.db_conn() as conn:
        row = DB.db_get(conn, article_key)
        if not row:
            raise HTTPException(status_code=404, detail="get: article_key introuvable")
        wh_hash = row.get("webhook_hash")
        return {
            "status": "ok",
            "operation": "get",
            "article_key": article_key,
            "message_ids": row.get("message_ids"),
            "embeds_counts": row.get("embeds_counts"),
            "updated_at": row.get("updated_at"),
            "webhook_hash": f"{wh_hash[:8]}…",
        }


def _op_list(_: Dict[str, Any]) -> Dict[str, Any]:
    with DB.db_conn() as conn:
        items = DB.db_list(conn)
    return {"status": "ok", "operation": "list", "items": items}


def run_operation(**params) -> Any:
    operation = (params.get("operation") or "create").lower()
    if operation in ("create", "update", "upsert"):
        return op_create_or_update(params, operation)
    if operation == "delete":
        return _op_delete(params)
    if operation == "get":
        return _op_get(params)
    if operation == "list":
        return _op_list(params)
    raise HTTPException(status_code=400, detail="operation invalide")
