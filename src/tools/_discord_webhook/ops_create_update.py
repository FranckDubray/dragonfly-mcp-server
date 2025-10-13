"""Orchestration for create/update/upsert operations."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException
import logging

try:
    from .util import get_discord_webhook_url, parse_webhook, webhook_hash
    from .embeds import make_embeds_from_article, batch_embeds, CONTENT_MAX
    from . import db as DB
    from .attachments import (
        maybe_download_to_attachments,
        build_files_from_attachments,
        inject_attachment_into_embeds,
    )
    from .ops_create import op_create
    from .ops_update import op_update
except Exception:
    from src.tools._discord_webhook.util import get_discord_webhook_url, parse_webhook, webhook_hash
    from src.tools._discord_webhook.embeds import make_embeds_from_article, batch_embeds, CONTENT_MAX
    from src.tools._discord_webhook import db as DB
    from src.tools._discord_webhook.attachments import (
        maybe_download_to_attachments,
        build_files_from_attachments,
        inject_attachment_into_embeds,
    )
    from src.tools._discord_webhook.ops_create import op_create
    from src.tools._discord_webhook.ops_update import op_update

logger = logging.getLogger(__name__)


def _dry_run_response(mode: str, article_key: str, batches: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Generate dry-run response without posting."""
    previews = []
    for b in batches:
        concat = "".join([(e.get("description") or "") for e in b])
        previews.append({"embeds_count": len(b), "preview": concat[:200]})
    total_embeds = sum(len(b) for b in batches)
    split_applied = total_embeds > 1
    
    if split_applied:
        logger.info(f"[DRY-RUN] Article '{article_key}' would be split into {len(batches)} message(s)")
    
    return {
        "status": "dry_run",
        "operation": mode,
        "article_key": article_key,
        "batches_planned": previews,
        "total_embeds": total_embeds,
        "split_applied": split_applied,
    }


def _build_batches(params: Dict[str, Any]) -> Tuple[str, List[List[Dict[str, Any]]], List[int]]:
    """Build embed batches from article or embeds parameter."""
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
    
    logger.info(f"Built {len(batches)} batch(es) with {sum(counts)} total embeds for '{article_key}'")
    
    return article_key, batches, counts


def _apply_attachments(params: Dict[str, Any], batches: List[List[Dict[str, Any]]]) -> Optional[List[Tuple[str, str, bytes, str]]]:
    """Process attachments (download if needed) and return files_data."""
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
            logger.info(f"Prepared {len(files_data)} attachment(s)")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if batches and batches[0]:
            inject_attachment_into_embeds(batches[0], attachments_list, override=True)
    return files_data


def _base_payload_builder(batches: List[List[Dict[str, Any]]], params: Dict[str, Any]):
    """Build payload builder function for batches."""
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


def op_create_or_update(params: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """Main orchestration for create/update/upsert operations."""
    assert mode in ("create", "update", "upsert")

    wait = bool(params.get("wait", True))
    dry_run = bool(params.get("dry_run", False))
    thread_id = params.get("thread_id")

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
        logger.info(f"Upsert resolved to: {effective_mode}")

    if effective_mode == "create":
        if existing_row:
            raise HTTPException(status_code=405, detail="create: article_key déjà existant. Utilisez 'update' ou 'upsert'.")
        payload_builder = _base_payload_builder(batches, params)
        return op_create(article_key, batches, counts, files_data, wait, payload_builder, wh_hash, thread_id)

    if effective_mode == "update":
        if existing_row and existing_row.get("webhook_hash") != wh_hash:
            raise HTTPException(status_code=409, detail="Le webhook courant diffère de celui utilisé pour publier cet article. Les messages ne peuvent pas être édités après rotation du webhook.")
        existing_ids = list((existing_row or {}).get("message_ids") or [])
        target_message_ids_param: List[str] = params.get("target_message_ids") or []
        if target_message_ids_param:
            existing_ids = list(map(str, target_message_ids_param))
            logger.info(f"Using manual target_message_ids: {len(existing_ids)} message(s)")
        payload_builder = _base_payload_builder(batches, params)
        return op_update(article_key, batches, counts, files_data, wait, payload_builder, wh_id, token, existing_ids, wh_hash, thread_id)

    raise HTTPException(status_code=400, detail="operation invalide")
