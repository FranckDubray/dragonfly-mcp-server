import time
from typing import List
from .db import begin_step, end_step
from .flow_fetch import search_unseen, get_message_and_log_body_branch, prepare_and_persist
from .flow_classify import classify_with_llm, act_and_log


def run_cycle(db_path: str, mailbox: str, folders: List[str], llm_model: str, params: dict, mark_read: bool, poll_seconds: int) -> bool:
    # Provider cycle: no global START here (logged once per cycle in core_loop)
    processed = False
    primary_folder = folders[0] if folders else 'INBOX'

    while True:
        msgs = search_unseen(db_path, mailbox, primary_folder)
        # Log conditional: has_unseen
        t_hu = time.time()
        has_any = bool(msgs)
        begin_step(db_path, mailbox, 'has_unseen', 'has_unseen', {"folder": primary_folder, "count": len(msgs)})
        end_step(db_path, mailbox, 'has_unseen', 'has_unseen', 'succeeded', t_hu, {"folder": primary_folder, "count": len(msgs), "decision": has_any})

        if not msgs:
            # No marker step here anymore; just end provider pass
            break

        uid = msgs[0].get('uid')
        folder = msgs[0].get('folder') or primary_folder

        msg = get_message_and_log_body_branch(db_path, mailbox, folder, uid)
        san, userp = prepare_and_persist(db_path, mailbox, folder, uid, msg)

        parsed = classify_with_llm(db_path, mailbox, folder, userp, llm_model, {**params, 'uid': uid})
        act_and_log(db_path, mailbox, folder, uid, parsed, mark_read, llm_model, san)
        processed = True

    return processed
