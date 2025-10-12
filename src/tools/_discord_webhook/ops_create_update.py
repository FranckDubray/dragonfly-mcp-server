

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Optional
from fastapi import HTTPException

# Robust imports (package or absolute)
try:
    from .util import get_discord_webhook_url, parse_webhook, webhook_hash, API_BASE  # type: ignore
    from .embeds import make_embeds_from_article, batch_embeds, CONTENT_MAX  # type: ignore
    from .http_client import http_request  # type: ignore
    from . import db as DB  # type: ignore
    from .attachments import (  # type: ignore
        maybe_download_to_attachments,
        build_files_from_attachments,
        inject_attachment_into_embeds,
    )
    from .sender import (  # type: ignore
        send_create_batches,
        send_update_batches,
    )
except Exception:
    from src.tools._discord_webhook.util import get_discord_webhook_url, parse_webhook, webhook_hash, API_BASE  # type: ignore
    from src.tools._discord_webhook.embeds import make_embeds_from_article, batch_embeds, CONTENT_MAX  # type: ignore
    from src.tools._discord_webhook.http_client import http_request  # type: ignore
    from src.tools._discord_webhook import db as DB  # type: ignore
    from src.tools._discord_webhook.attachments import (  # type: ignore
        maybe_download_to_attachments,
        build_files_from_attachments,
        inject_attachment_into_embeds,
    )
    from src.tools._discord_webhook.sender import (  # type: ignore
        send_create_batches,
        send_update_batches,
    )


def _dry_run_response(mode: str, article_key: str, batches: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    previews = []
    for b in batches:
        concat = "".join([(e.get("description") or "") for e in b])
        previews.append({"embeds_count": len(b), "preview": concat[:200]})
    total_embeds = sum(len(b) for b in batches)
    split_applied = total_embeds > 1
    return {
        "status": "dry_run",
        "operation": mode,
        "article_key": article_key,
        "batches_planned": previews,
        "total_embeds": total_embeds,
        "split_applied": split_applied,
    }


def _build_batches(params: Dict[str, Any]) -> Tuple[str, List[List[Dict[str, Any]]], List[int]]:
    article_key = params.get("article_key")
    if not article_key:
        raise HTTPException(status_code=400, detail="article_key requis pour cette opération")

    article = params.get("article")
    embeds = params.get("embeds")
    split_long_messages = bool(params.get("split_long_messages", True))

    if not article and not embeds:
        raise HTTPException(status_code=400, detail="article ou embeds requis")

    if article:
        embeds_built = make_embeds_from_article(article, split_long_messages=split_long_messages)
    else:
        embeds_built = embeds or []

    batches = batch_embeds(embeds_built)
    counts = [len(b) for b in batches]
    return article_key, batches, counts


def _apply_attachments(params: Dict[str, Any], batches: List[List[Dict[str, Any]]]) -> Optional[List[Tuple[str, str, bytes, str]]]:
    attachments_param: List[Dict[str, Any]] = params.get("attachments") or []
    upload_image_url: Optional[str] = params.get("upload_image_url")

    try:
        attachments_list = maybe_download_to_attachments(upload_image_url, attachments_param)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    files_data = None
    if attachments_list:
        try:
            files_data = build_files_from_attachments(attachments_list)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        # Inject attachment into first embed of first batch (override any existing image)
        if batches and batches[0]:
            inject_attachment_into_embeds(batches[0], attachments_list, override=True)
    return files_data


def _base_payload_builder(batches: List[List[Dict[str, Any]]], params: Dict[str, Any]):
    content = params.get("content")
    username = params.get("username")
    avatar_url = params.get("avatar_url")
    tts = bool(params.get("tts", False))
    allowed_mentions = params.get("allowed_mentions")

    def build_payload_for_batch(i: int) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"embeds": batches[i]}
        if i == 0 and content:
            payload["content"] = content[:CONTENT_MAX]
        if username:
            payload["username"] = username
        if avatar_url:
            payload["avatar_url"] = avatar_url
        if allowed_mentions is not None:
            payload["allowed_mentions"] = allowed_mentions
        if tts:
            payload["tts"] = True
        return payload

    return build_payload_for_batch


def _build_url_with_thread(base_url: str, thread_id: Optional[str]) -> str:
    """Append thread_id query param if provided."""
    if thread_id:
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}thread_id={thread_id}"
    return base_url


def _create(article_key: str, batches: List[List[Dict[str, Any]]], counts: List[int], files_data, wait: bool, payload_builder, wh_hash: str, thread_id: Optional[str]) -> Dict[str, Any]:
    url = get_discord_webhook_url()
    # Add thread_id to URL if provided
    url = _build_url_with_thread(url, thread_id)
    
    posted_batches = 0
    new_message_ids: List[str] = []

    if files_data:
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
                    raise HTTPException(status_code=502, detail=f"Discord POST a échoué (statut {res.status_code}).")
                msg_id = str(res.json.get("id")) if res.json else None
                if not msg_id:
                    raise HTTPException(status_code=502, detail="Discord n'a pas renvoyé d'id de message.")
                new_message_ids.append(msg_id)

    with DB.db_conn() as conn:
        DB.db_create(conn, article_key, wh_hash, new_message_ids, counts)

    base: Dict[str, Any] = {
        "status": "ok",
        "operation": "create",
        "posted_batches": posted_batches,
        "total_embeds": sum(counts),
        "split_applied": sum(counts) > 1,
        "article_key": article_key,
    }
    if wait:
        base["messages"] = [
            {"id": mid, "embeds_count": counts[i], "batch_index": i} for i, mid in enumerate(new_message_ids)
        ]
    return base


def _update(article_key: str, batches: List[List[Dict[str, Any]]], counts: List[int], files_data, wait: bool, payload_builder, wh_id: str, token: str, existing_ids: List[str], wh_hash: str, thread_id: Optional[str]) -> Dict[str, Any]:
    posted_batches = 0
    new_message_ids: List[str] = []

    if not wait and len(batches) != len(existing_ids):
        raise HTTPException(status_code=400, detail="update avec wait=false requiert que le nombre de messages ne change pas (sinon impossible de maintenir l'état)")

    url = get_discord_webhook_url()
    # Add thread_id to URL if provided
    url = _build_url_with_thread(url, thread_id)

    if files_data:
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
                raise HTTPException(status_code=502, detail=f"Discord PATCH a échoué (statut {res.status_code}).")
            new_message_ids.append(msg_id)
        if len(batches) > len(existing_ids):
            for i in range(len(existing_ids), len(batches)):
                payload = payload_builder(i)
                res = http_request("POST", f"{url}?wait={'true' if wait else 'false'}", json_body=payload)
                posted_batches += 1
                if wait:
                    if res.status_code >= 300 or not res.json:
                        raise HTTPException(status_code=502, detail=f"Discord POST a échoué (statut {res.status_code}).")
                    msg_id = str(res.json.get("id")) if res.json else None
                    if not msg_id:
                        raise HTTPException(status_code=502, detail="Discord n'a pas renvoyé d'id de message.")
                    new_message_ids.append(msg_id)
        elif len(batches) < len(existing_ids):
            for i in range(len(existing_ids) - 1, len(batches) - 1, -1):
                msg_id = existing_ids[i]
                res = http_request("DELETE", f"{API_BASE}/webhooks/{wh_id}/{token}/messages/{msg_id}")
                posted_batches += 1
                if not (200 <= res.status_code < 300 or res.status_code == 404):
                    raise HTTPException(status_code=502, detail=f"Discord DELETE a échoué (statut {res.status_code}).")

    # Persist mapping
    try:
        with DB.db_conn() as conn:
            if len(new_message_ids) < len(batches):
                new_message_ids = existing_ids[:len(batches)]
            DB.db_update(conn, article_key, wh_hash, new_message_ids or existing_ids, counts)
    except Exception as e:
        if "missing" in str(e).lower():
            with DB.db_conn() as conn:
                DB.db_create(conn, article_key, wh_hash, new_message_ids or existing_ids, counts)
        else:
            raise

    base: Dict[str, Any] = {
        "status": "ok",
        "operation": "update",
        "posted_batches": posted_batches,
        "total_embeds": sum(counts),
        "split_applied": sum(counts) > 1,
        "article_key": article_key,
    }
    if wait:
        base["messages"] = [
            {"id": mid, "embeds_count": counts[i], "batch_index": i}
            for i, mid in enumerate(new_message_ids or existing_ids)
        ]
    return base


def op_create_or_update(params: Dict[str, Any], mode: str) -> Dict[str, Any]:
    assert mode in ("create", "update", "upsert")

    wait = bool(params.get("wait", True))
    dry_run = bool(params.get("dry_run", False))
    thread_id = params.get("thread_id")  # NEW: thread support

    # Enforce wait=true on create/upsert to persist message ids
    if mode in ("create", "upsert") and not wait:
        raise HTTPException(status_code=400, detail="wait=true requis pour create/upsert afin de persister les message_ids pour les mises à jour ultérieures")

    article_key, batches, counts = _build_batches(params)

    if dry_run:
        return _dry_run_response(mode, article_key, batches)

    files_data = _apply_attachments(params, batches)

    url = get_discord_webhook_url()
    wh_id, token = parse_webhook(url)
    wh_hash = webhook_hash(wh_id, token)

    existing_row = None
    with DB.db_conn() as conn:
        existing_row = DB.db_get(conn, article_key)

    effective_mode = mode
    if mode == "upsert":
        effective_mode = "update" if existing_row else "create"

    if effective_mode == "create":
        if existing_row:
            raise HTTPException(status_code=405, detail="create: article_key déjà existant. Utilisez 'update' ou 'upsert'.")
        payload_builder = _base_payload_builder(batches, params)
        return _create(article_key, batches, counts, files_data, wait, payload_builder, wh_hash, thread_id)

    if effective_mode == "update":
        if existing_row and existing_row.get("webhook_hash") != wh_hash:
            raise HTTPException(status_code=409, detail="Le webhook courant diffère de celui utilisé pour publier cet article. Les messages ne peuvent pas être édités après rotation du webhook.")
        existing_ids = list((existing_row or {}).get("message_ids") or [])
        target_message_ids_param: List[str] = params.get("target_message_ids") or []
        if target_message_ids_param:
            existing_ids = list(map(str, target_message_ids_param))
        payload_builder = _base_payload_builder(batches, params)
        return _update(article_key, batches, counts, files_data, wait, payload_builder, wh_id, token, existing_ids, wh_hash, thread_id)

    raise HTTPException(status_code=400, detail="operation invalide")

 
 
 
 
