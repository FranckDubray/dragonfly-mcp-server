import time, hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple
from .db import begin_step, end_step, set_state_kv, upsert_mail_message
from .services.mcp_client import call_with_retry
from .utils import extract_headers, extract_body_raw, extract_body_text, sanitize_body, user_prompt
import email.utils as eut


CUTOFF_DAYS = 7
MAX_SUBJECT_FALLBACK = 120


def _parse_iso_date(val: str) -> datetime | None:
    if not val:
        return None
    try:
        # Try RFC2822 via email.utils
        dt = eut.parsedate_to_datetime(val)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass
    try:
        # Fallback common ISO-like "YYYY-MM-DD ..."
        return datetime.fromisoformat(val[:19]).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _is_recent(msg_summary: Dict[str, Any], cutoff_utc: datetime) -> bool:
    # Check common date fields on message list summaries
    for k in ("internal_date", "date", "Date", "received"):
        v = msg_summary.get(k)
        if isinstance(v, str) and v:
            dt = _parse_iso_date(v)
            if dt:
                return dt >= cutoff_utc
    # If unknown, consider recent (let downstream filter on full fetch if needed)
    return True


def search_unseen(db_path: str, mailbox: str, folder: str) -> list:
    t0 = time.time()
    cutoff_utc = datetime.now(timezone.utc) - timedelta(days=CUTOFF_DAYS)
    cutoff_str = cutoff_utc.strftime('%Y-%m-%d')

    begin_step(db_path, mailbox, 'imap_search_unseen_oldest', 'imap_search_unseen_oldest', {"folder": folder, "action": "search_messages", "since": cutoff_str})

    messages = []
    returned_count = 0
    filtered_count = 0
    tried_fallback = False

    # Try server-side date restriction if supported by IMAP tool
    try:
        res = call_with_retry('imap', {
            'operation': 'search_messages', 'provider': mailbox, 'folder': folder,
            'query': {'unseen': True, 'since': cutoff_str}, 'max_results': 25
        }, retries=1, timeout=15.0) or {}
        root = res.get('result') or res
        base = root.get('messages') or []
        returned_count = len(base)
        # Client-side safety filter (if server ignored 'since')
        msgs = [m for m in base if _is_recent(m, cutoff_utc)]
        filtered_count = len(msgs)
        # Keep the oldest among the recent ones
        messages = msgs[:1]
    except Exception:
        tried_fallback = True
        # Fallback: no 'since' param, grab a window and filter client-side
        try:
            res = call_with_retry('imap', {
                'operation': 'search_messages', 'provider': mailbox, 'folder': folder,
                'query': {'unseen': True}, 'max_results': 25
            }, retries=1, timeout=15.0) or {}
            root = res.get('result') or res
            base = root.get('messages') or []
            returned_count = len(base)
            msgs = [m for m in base if _is_recent(m, cutoff_utc)]
            filtered_count = len(msgs)
            messages = msgs[:1]
        except Exception:
            messages = []

    end_step(db_path, mailbox, 'imap_search_unseen_oldest', 'imap_search_unseen_oldest', 'succeeded', t0, {
        "returned_count": returned_count,
        "returned_count_recent": filtered_count,
        "used_fallback": tried_fallback,
        "folder": folder,
        "since": cutoff_str,
    })
    return messages


def get_message_and_log_body_branch(db_path: str, mailbox: str, folder: str, uid: str) -> Dict[str, Any]:
    while True:
        try:
            t2 = time.time()
            begin_step(db_path, mailbox, 'imap_get_message_full', 'imap_get_message_full', {"uid": uid, "folder": folder, "action": "get_message"})
            res_msg = call_with_retry('imap', {
                'operation': 'get_message', 'provider': mailbox, 'folder': folder,
                'message_id': uid, 'include_body': True, 'include_attachments_metadata': False
            }, retries=1, timeout=30.0) or {}
            msg = res_msg.get('result') or res_msg
            # Branch body size/source
            raw_body, source = extract_body_raw(msg)
            body_over = len(raw_body) > 30000
            step_id = 'body_over_30kb' if body_over else 'use_full_body'
            t_body = time.time()
            begin_step(db_path, mailbox, step_id, step_id, {"source": source, "len": len(raw_body), "folder": folder})
            end_step(db_path, mailbox, step_id, step_id, 'succeeded', t_body, {"source": source, "len": len(raw_body), "folder": folder})
            # If truncated flow: log prepare_truncated_view explicitly
            if body_over:
                t_prep = time.time()
                begin_step(db_path, mailbox, 'prepare_truncated_view', 'prepare_truncated_view', {"reason": ">30KB", "len": len(raw_body), "folder": folder})
                end_step(db_path, mailbox, 'prepare_truncated_view', 'prepare_truncated_view', 'succeeded', t_prep, {"reason": ">30KB", "len": len(raw_body), "folder": folder})
            end_step(db_path, mailbox, 'imap_get_message_full', 'imap_get_message_full', 'succeeded', t2, {"has_body": bool((msg or {}).get('body')), "action": "get_message", "folder": folder})
            return msg
        except Exception as e:
            # log erreur et pause 60s
            end_step(db_path, mailbox, 'imap_get_message_full', 'imap_get_message_full', 'failed', t2, {"error": str(e)[:400], "folder": folder})
            nxt = (datetime.now(timezone.utc) + timedelta(seconds=60)).strftime('%Y-%m-%d %H:%M:%S')
            set_state_kv(db_path, '__global__', 'retry_next_at', nxt)
            time.sleep(60)


def prepare_and_persist(db_path: str, mailbox: str, folder: str, uid: str, msg: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    # Extract headers/body
    from_addr, subject_raw, date_hdr = extract_headers(msg)
    body_text = extract_body_text(msg)  # already HTML-stripped (utils.extract_body_raw)

    # Sanitize body and build user prompt first
    t3 = time.time(); begin_step(db_path, mailbox, 'sanitize_text', 'sanitize_text', {"folder": folder})
    san = sanitize_body(body_text)

    # Subject effective: use only header subject (no inference). If empty, keep empty.
    subject_eff = (subject_raw or '').strip()

    userp = user_prompt(from_addr, subject_eff, san['text'])
    end_step(db_path, mailbox, 'sanitize_text', 'sanitize_text', 'succeeded', t3, {"input_chars": len(userp), "folder": folder, "subject_present": bool(subject_eff), "subject_inferred": False, "subject_len": len(subject_eff)})

    # Persist message (use sanitized text for snippet/len/hash and truncated flag)
    san_text = san['text'] or ''
    snippet = san_text[:160]
    body_len = san.get('chars') or len(san_text)
    body_hash = hashlib.sha256((san_text).encode('utf-8', 'ignore')).hexdigest()
    upsert_mail_message(db_path, mailbox, folder, uid, from_addr, subject_eff, date_hdr, snippet, body_len, bool(san.get('truncated')), body_hash)

    return san, userp
