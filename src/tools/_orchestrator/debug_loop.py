# Debug loop: pause/wait and resume orchestration in the same cycle
from .db import get_state_kv, set_state_kv, heartbeat


def debug_wait_loop(db_path: str, worker: str):
    import time
    last_beat = 0
    while True:
        cmd = get_state_kv(db_path, worker, 'debug.command') or 'none'
        now = time.time()
        if now - last_beat > 10:
            heartbeat(db_path, worker)
            last_beat = now
        if cmd == 'none':
            time.sleep(0.25)
            continue
        if cmd in ('step','continue','run_until'):
            set_state_kv(db_path, worker, 'debug.mode', 'step' if cmd=='step' else ('continue' if cmd=='continue' else 'until'))
            set_state_kv(db_path, worker, 'debug.command', 'none')
            return
        if cmd == 'disable':
            set_state_kv(db_path, worker, 'debug.enabled', 'false')
            set_state_kv(db_path, worker, 'debug.command', 'none')
            return
        if cmd == 'break_clear':
            set_state_kv(db_path, worker, 'debug.breakpoints', '[]')
            set_state_kv(db_path, worker, 'debug.command', 'none')
        time.sleep(0.1)
