import time, json, hashlib, os, threading, traceback, re
from typing import Dict, Any
from datetime import timedelta, datetime, timezone
from .db import (
    get_db_path, get_state_kv, set_state_kv, begin_step, end_step,
    upsert_mail_message, insert_classification, insert_action, insert_llm_usage, utcnow_str
)
from .prompt_templates import SYSTEM_PROMPT, USER_TEMPLATE
from .services.imap_helpers import resolve_spam_folder
from .services.mcp_client import call_with_retry

# ... utilitaires identiques ...


def run_loop(db_path: str, params: dict):
    db_path = db_path or get_db_path(params.get('worker_name') or 'default')
    try:
        worker_name = params.get('worker_name') or 'default'
        mailboxes = params.get('mailboxes', [])
        folders = params.get('folders', ['INBOX'])
        poll_seconds = int(params.get('poll_interval_minutes', 10)) * 60
        mark_read = bool(params.get('mark_read', True))
        llm_model = params.get('llm_model', 'gpt-5-mini')

        # lock anti doublon
        phase = get_state_kv(db_path, '__global__', 'phase')
        if phase in {'running','sleeping'}:
            return

        set_state_kv(db_path, '__global__', 'phase', 'running')
        set_state_kv(db_path, '__global__', 'pid', str(os.getpid()))
        set_state_kv(db_path, '__global__', 'thread_id', str(threading.get_ident()))
        set_state_kv(db_path, '__global__', 'retry_next_at', '')
        _heartbeat(db_path)

        primary_folder = folders[0]
        spam_folder_by_mb = {mb: (_get_spam_folder_cached(db_path, mb)) for mb in mailboxes}

        while True:
            if (get_state_kv(db_path, '__global__', 'cancel') or 'false') == 'true':
                set_state_kv(db_path, '__global__', 'phase', 'canceled')
                _heartbeat(db_path)
                return

            set_state_kv(db_path, '__global__', 'phase', 'running')
            set_state_kv(db_path, '__global__', 'processed_in_pass', 'false')
            _heartbeat(db_path)
            any_processed = False

            for mailbox in mailboxes:
                while True:
                    # T1 search unseen oldest
                    t0 = time.time(); begin_step(db_path, mailbox, 'T1', 'imap search unseen oldest', {"folder": primary_folder, "action": "search_messages"})
                    res_search = call_with_retry('imap', {
                        'operation': 'search_messages', 'provider': mailbox, 'folder': primary_folder,
                        'query': {'unseen': True}, 'max_results': 1
                    }, retries=1, timeout=15.0) or {}
                    root = res_search.get('result') or res_search
                    messages = root.get('messages') or []
                    end_step(db_path, mailbox, 'T1', 'imap search unseen oldest', 'succeeded', t0, {"returned_count": len(messages)})
                    if not messages:
                        t0f = time.time(); begin_step(db_path, mailbox, 'TF', 'finish mailbox db', {"action": "finish"}); end_step(db_path, mailbox, 'TF', 'finish mailbox db', 'succeeded', t0f, {})
                        break

                    uid = messages[0].get('uid'); folder = messages[0].get('folder') or primary_folder

                    # T2 get message full (retry jusqu'à succès avec pause 60s)
                    while True:
                        try:
                            t2 = time.time(); begin_step(db_path, mailbox, 'T2', 'imap get message full', {"uid": uid, "folder": folder, "action": "get_message"})
                            res_msg = call_with_retry('imap', {
                                'operation': 'get_message', 'provider': mailbox, 'folder': folder,
                                'message_id': uid, 'include_body': True, 'include_attachments_metadata': False
                            }, retries=1, timeout=30.0) or {}
                            msg = res_msg.get('result') or res_msg
                            end_step(db_path, mailbox, 'T2', 'imap get message full', 'succeeded', t2, {"has_body": bool((msg or {}).get('body')), "action": "get_message"})
                            break
                        except Exception as e:
                            # log erreur et pause 60s
                            end_step(db_path, mailbox, 'T2', 'imap get message full', 'failed', t2, {"error": str(e)[:400]})
                            nxt = (datetime.now(timezone.utc) + timedelta(seconds=60)).strftime('%Y-%m-%d %H:%M:%S')
                            set_state_kv(db_path, '__global__', 'retry_next_at', nxt); _heartbeat(db_path); time.sleep(60)
                            continue

                    from_addr = (msg.get('from') or '')[:256]; subject = (msg.get('subject') or '')[:512]; date_hdr = (msg.get('date') or '')[:64]
                    body_text = _extract_body_text(msg)
                    snippet = (body_text[:160] if body_text else ''); body_len = len(body_text or ''); body_hash = hashlib.sha256((body_text or '').encode('utf-8', 'ignore')).hexdigest()
                    upsert_mail_message(db_path, mailbox, folder, uid, from_addr, subject, date_hdr, snippet, body_len, False, body_hash)

                    # T3 sanitize
                    t3 = time.time(); begin_step(db_path, mailbox, 'T3', 'sanitize text', {}); san = _sanitize_body(body_text); user_prompt = _user_prompt(from_addr, subject, san['text']); end_step(db_path, mailbox, 'T3', 'sanitize text', 'succeeded', t3, {"input_chars": len(user_prompt)})

                    # T4 call llm (retry 60s jusqu'à succès, timeout 200s)
                    while True:
                        try:
                            t4 = time.time(); begin_step(db_path, mailbox, 'T4', 'call llm classify both', {"model": llm_model, "action": "call"})
                            res_llm = call_with_retry('call_llm', {
                                'operation': 'call', 'model': llm_model, 'messages': [
                                    {"role": "system", "content": SYSTEM_PROMPT},
                                    {"role": "user", "content": user_prompt}
                                ], 'temperature': 0, 'max_tokens': params.get('max_tokens', 64)
                            }, retries=1, timeout=200.0) or {}
                            llm_res = res_llm.get('result') or res_llm
                            end_step(db_path, mailbox, 'T4', 'call llm classify both', 'succeeded', t4, {"model": llm_model})
                            break
                        except Exception as e:
                            end_step(db_path, mailbox, 'T4', 'call llm classify both', 'failed', t4, {"error": str(e)[:400]})
                            nxt = (datetime.now(timezone.utc) + timedelta(seconds=60)).strftime('%Y-%m-%d %H:%M:%S')
                            set_state_kv(db_path, '__global__', 'retry_next_at', nxt); _heartbeat(db_path); time.sleep(60)
                            continue

                    usage = (llm_res.get('usage') or {}); tokens_in = usage.get('prompt_tokens') or 0; tokens_out = usage.get('completion_tokens') or 0
                    try:
                        parsed = json.loads((llm_res.get('text') or '').strip())
                    except Exception:
                        parsed = {"class":"HAM","score":5,"urgency":"NORMAL","intent":"autre","hints":"ignorer","entities":{},"truncated": san['truncated'],"body_chars": san['chars'],"notes":"fallback"}
                    insert_llm_usage(db_path, mailbox, folder, uid, llm_model, tokens_in, tokens_out)

                    klass = (parsed.get('class') or '').upper(); score = int(parsed.get('score') or 5)
                    if klass not in {'SPAM','HAM'}: klass = 'HAM'
                    if score < 1 or score > 10: score = 5

                    # T5 log + act
                    if klass == 'SPAM':
                        t5s = time.time(); begin_step(db_path, mailbox, 'T5S', 'log spam db', {"uid": uid, "folder": folder})
                        insert_classification(db_path, mailbox, folder, uid, 'SPAM', score, parsed.get('intent'), parsed.get('hints'), parsed.get('entities') or {}, san['truncated'], san['chars'], llm_model)
                        end_step(db_path, mailbox, 'T5S', 'log spam db', 'succeeded', t5s, {"uid": uid})
                        spam_folder = _get_spam_folder_cached(db_path, mailbox) or folder
                        t5m = time.time(); begin_step(db_path, mailbox, 'T5M', 'imap move to spam', {"uid": uid, "from": folder, "to": spam_folder, "action": "move_message"})
                        call_with_retry('imap', {'operation': 'move_message', 'provider': mailbox, 'folder': folder, 'message_id': uid, 'target_folder': spam_folder}, retries=3, timeout=30.0)
                        end_step(db_path, mailbox, 'T5M', 'imap move to spam', 'succeeded', t5m, {"uid": uid}); insert_action(db_path, mailbox, folder, uid, 'move_spam')
                    else:
                        t5h = time.time(); begin_step(db_path, mailbox, 'T5H', 'log ham db', {"uid": uid, "folder": folder, "score": score})
                        insert_classification(db_path, mailbox, folder, uid, 'HAM', score, parsed.get('intent'), parsed.get('hints'), parsed.get('entities') or {}, san['truncated'], san['chars'], llm_model)
                        end_step(db_path, mailbox, 'T5H', 'log ham db', 'succeeded', t5h, {"uid": uid})
                        if mark_read:
                            t6 = time.time(); begin_step(db_path, mailbox, 'T6', 'imap mark read', {"uid": uid, "folder": folder, "action": "mark_read"})
                            call_with_retry('imap', {'operation': 'mark_read', 'provider': mailbox, 'folder': folder, 'message_id': uid}, retries=3, timeout=30.0)
                            end_step(db_path, mailbox, 'T6', 'imap mark read', 'succeeded', t6, {"uid": uid}); insert_action(db_path, mailbox, folder, uid, 'mark_read')

                    any_processed = True; set_state_kv(db_path, '__global__', 'processed_in_pass', 'true'); _heartbeat(db_path)

            if not any_processed:
                set_state_kv(db_path, '__global__', 'phase', 'sleeping')
                nxt = (datetime.now(timezone.utc) + timedelta(seconds=poll_seconds)).strftime('%Y-%m-%d %H:%M:%S')
                set_state_kv(db_path, '__global__', 'sleep_until', nxt); _heartbeat(db_path); time.sleep(poll_seconds)

    except Exception as e:
        try:
            tb = traceback.format_exc(limit=3)
            begin_ts = time.time(); begin_step(db_path, '__global__', 'E0', 'fatal error', {"message": str(e)[:500]}); end_step(db_path, '__global__', 'E0', 'fatal error', 'failed', begin_ts, {"trace": tb[-1500:]})
            set_state_kv(db_path, '__global__', 'phase', 'failed'); _heartbeat(db_path)
        except Exception:
            pass
        raise
