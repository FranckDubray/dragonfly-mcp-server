import os, threading, traceback, time
from .db import get_db_path, get_state_kv, set_state_kv, begin_step, end_step
from .utils import heartbeat, get_spam_folder_cached, is_canceled, cooperative_sleep
from .flow_cycle import run_cycle


def run_loop(db_path: str, params: dict):
    db_path = db_path or get_db_path(params.get('worker_name') or 'default')
    try:
        worker_name = params.get('worker_name') or 'default'
        mailboxes = params.get('mailboxes', [])
        folders = params.get('folders', ['INBOX'])
        poll_seconds = int(params.get('poll_interval_minutes', 10)) * 60
        mark_read = bool(params.get('mark_read', True))
        llm_model = params.get('llm_model', 'gpt-5-mini')

        phase = get_state_kv(db_path, '__global__', 'phase')
        if phase in {'running','sleeping'}:
            return

        set_state_kv(db_path, '__global__', 'phase', 'running')
        set_state_kv(db_path, '__global__', 'pid', str(os.getpid()))
        set_state_kv(db_path, '__global__', 'thread_id', str(threading.get_ident()))
        set_state_kv(db_path, '__global__', 'retry_next_at', '')
        heartbeat(db_path)

        _ = {mb: (get_spam_folder_cached(db_path, mb)) for mb in mailboxes}

        while True:
            if is_canceled(db_path):
                set_state_kv(db_path, '__global__', 'phase', 'canceled')
                heartbeat(db_path)
                return

            set_state_kv(db_path, '__global__', 'phase', 'running')
            set_state_kv(db_path, '__global__', 'processed_in_pass', 'false')
            heartbeat(db_path)

            # Global START (once per cycle)
            ts = time.time(); begin_step(db_path, '__global__', 'START', 'START', {"note": "cycle init"}); end_step(db_path, '__global__', 'START', 'START', 'succeeded', ts, {})

            any_processed = False
            for mailbox in mailboxes:
                if is_canceled(db_path):
                    break
                # has_more_mailboxes per provider (decision point)
                t_hmb = time.time(); begin_step(db_path, mailbox, 'has_more_mailboxes', 'has_more_mailboxes', {"folders": folders}); end_step(db_path, mailbox, 'has_more_mailboxes', 'has_more_mailboxes', 'succeeded', t_hmb, {"folders": folders})
                processed = run_cycle(db_path, mailbox, folders, llm_model, params, mark_read, poll_seconds)
                any_processed = any_processed or processed

            if is_canceled(db_path):
                set_state_kv(db_path, '__global__', 'phase', 'canceled')
                heartbeat(db_path)
                return

            if not any_processed:
                # Log final has_more_mailboxes (global: no more mailboxes → sleep) to match graph
                t_hmb_end = time.time(); begin_step(db_path, '__global__', 'has_more_mailboxes', 'has_more_mailboxes', {"folders": folders, "decision": False})
                end_step(db_path, '__global__', 'has_more_mailboxes', 'has_more_mailboxes', 'succeeded', t_hmb_end, {"folders": folders, "decision": False})

                # END of cycle sleep (single place)
                set_state_kv(db_path, '__global__', 'phase', 'sleeping')
                from datetime import datetime, timezone, timedelta
                nxt = (datetime.now(timezone.utc) + timedelta(seconds=poll_seconds)).strftime('%Y-%m-%d %H:%M:%S')
                set_state_kv(db_path, '__global__', 'sleep_until', nxt)
                t_sl = time.time(); begin_step(db_path, '__global__', 'sleep_interval', 'sleep_interval', {"until": nxt, "seconds": poll_seconds})
                cooperative_sleep(db_path, poll_seconds)
                end_step(db_path, '__global__', 'sleep_interval', 'sleep_interval', 'succeeded', t_sl, {"until": nxt, "seconds": poll_seconds})
                # Next cycle will start fresh

    except Exception as e:
        try:
            tb = traceback.format_exc(limit=3)
            begin_ts = __import__('time').time(); begin_step(db_path, '__global__', 'fatal_error', 'fatal_error', {"message": str(e)[:500]}); end_step(db_path, '__global__', 'fatal_error', 'fatal_error', 'failed', begin_ts, {"trace": tb[-1500:]})
            set_state_kv(db_path, '__global__', 'phase', 'failed'); heartbeat(db_path)
        except Exception:
            pass
        raise
