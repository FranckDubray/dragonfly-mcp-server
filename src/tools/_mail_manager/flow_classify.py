import time, json
from typing import Dict, Any
from .db import begin_step, end_step, insert_llm_usage, insert_classification, insert_action
from .services.mcp_client import call_with_retry
from .prompt_templates import SYSTEM_PROMPT


def classify_with_llm(db_path: str, mailbox: str, folder: str, user_prompt: str, llm_model: str, params: Dict[str, Any]) -> Dict[str, Any]:
    while True:
        try:
            t4 = time.time(); begin_step(db_path, mailbox, 'call_llm_classify_both', 'call_llm_classify_both', {"model": llm_model, "action": "call", "folder": folder})
            res_llm = call_with_retry('call_llm', {
                'operation': 'call', 'model': llm_model, 'messages': [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ], 'temperature': 0, 'max_tokens': params.get('max_tokens', 64)
            }, retries=1, timeout=200.0) or {}
            llm_res = res_llm.get('result') or res_llm
            end_step(db_path, mailbox, 'call_llm_classify_both', 'call_llm_classify_both', 'succeeded', t4, {"model": llm_model, "folder": folder})
            usage = (llm_res.get('usage') or {})
            insert_llm_usage(db_path, mailbox, folder, params.get('uid') or '', llm_model, usage.get('prompt_tokens') or 0, usage.get('completion_tokens') or 0)
            try:
                parsed = json.loads((llm_res.get('text') or '').strip())
            except Exception:
                parsed = {"class":"HAM","score":5,"urgency":"NORMAL","intent":"autre","hints":"ignorer","entities":{},"truncated": False, "body_chars": 0, "notes":"fallback"}
            return parsed
        except Exception as e:
            end_step(db_path, mailbox, 'call_llm_classify_both', 'call_llm_classify_both', 'failed', t4, {"error": str(e)[:400], "folder": folder})
            from datetime import datetime, timezone, timedelta
            nxt = (datetime.now(timezone.utc) + timedelta(seconds=60)).strftime('%Y-%m-%d %H:%M:%S')
            from .db import set_state_kv
            set_state_kv(db_path, '__global__', 'retry_next_at', nxt)
            time.sleep(60)


def act_and_log(db_path: str, mailbox: str, folder: str, uid: str, parsed: Dict[str, Any], mark_read: bool, llm_model: str, san: Dict[str, Any]) -> None:
    # class_branch (decision)
    t_cb = time.time();
    decision = (parsed.get('class') or '').lower() if parsed.get('class') else 'ham'
    begin_step(db_path, mailbox, 'class_branch', 'class_branch', {"decision": decision, "uid": uid, "folder": folder})

    klass = (parsed.get('class') or '').upper()
    score = int(parsed.get('score') or 5)
    if klass not in {'SPAM','HAM'}:
        klass = 'HAM'
    if score < 1 or score > 10:
        score = 5

    if klass == 'SPAM':
        end_step(db_path, mailbox, 'class_branch', 'class_branch', 'succeeded', t_cb, {"decision": 'spam'})
        t5s = time.time(); begin_step(db_path, mailbox, 'log_spam_db', 'log_spam_db', {"uid": uid, "folder": folder})
        insert_classification(db_path, mailbox, folder, uid, 'SPAM', score, parsed.get('urgency'), parsed.get('intent'), parsed.get('hints'), parsed.get('entities') or {}, san.get('truncated'), san.get('chars'), llm_model)
        end_step(db_path, mailbox, 'log_spam_db', 'log_spam_db', 'succeeded', t5s, {"uid": uid, "folder": folder})
        from .utils import get_spam_folder_cached
        spam_folder = get_spam_folder_cached(db_path, mailbox) or folder
        t5m = time.time(); begin_step(db_path, mailbox, 'imap_move_to_spam', 'imap_move_to_spam', {"uid": uid, "from": folder, "to": spam_folder, "action": "move_message"})
        from .services.mcp_client import call_with_retry
        call_with_retry('imap', {'operation': 'move_message', 'provider': mailbox, 'folder': folder, 'message_id': uid, 'target_folder': spam_folder}, retries=3, timeout=30.0)
        end_step(db_path, mailbox, 'imap_move_to_spam', 'imap_move_to_spam', 'succeeded', t5m, {"uid": uid, "from": folder, "to": spam_folder}); insert_action(db_path, mailbox, folder, uid, 'move_spam')
    else:
        end_step(db_path, mailbox, 'class_branch', 'class_branch', 'succeeded', t_cb, {"decision": 'ham'})
        t5h = time.time(); begin_step(db_path, mailbox, 'log_ham_db', 'log_ham_db', {"uid": uid, "folder": folder, "score": score})
        insert_classification(db_path, mailbox, folder, uid, 'HAM', score, parsed.get('urgency'), parsed.get('intent'), parsed.get('hints'), parsed.get('entities') or {}, san.get('truncated'), san.get('chars'), llm_model)
        end_step(db_path, mailbox, 'log_ham_db', 'log_ham_db', 'succeeded', t5h, {"uid": uid, "folder": folder})
        if mark_read:
            t6 = time.time(); begin_step(db_path, mailbox, 'imap_mark_read', 'imap_mark_read', {"uid": uid, "folder": folder, "action": "mark_read"})
            from .services.mcp_client import call_with_retry
            call_with_retry('imap', {'operation': 'mark_read', 'provider': mailbox, 'folder': folder, 'message_id': uid}, retries=3, timeout=30.0)
            end_step(db_path, mailbox, 'imap_mark_read', 'imap_mark_read', 'succeeded', t6, {"uid": uid, "folder": folder}); insert_action(db_path, mailbox, folder, uid, 'mark_read')
