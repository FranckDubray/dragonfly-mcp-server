











# Debug loop: pause/wait and resume orchestration in the same cycle
from .db import get_state_kv, set_state_kv, heartbeat
import sys


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
            time.sleep(0.05)  # tighter poll for fast nodes
            continue
        # trace consume
        try:
            set_state_kv(db_path, worker, 'debug.trace', f"consume:{cmd}:{now}")
        except Exception:
            pass
        if cmd in ('step','continue','run_until'):
            # small console trace for investigation
            try:
                print(f"[orchestrator][debug] consume cmd={cmd}", file=sys.stderr)
            except Exception:
                pass
            set_state_kv(db_path, worker, 'debug.mode', 'step' if cmd=='step' else ('continue' if cmd=='continue' else 'until'))
            set_state_kv(db_path, worker, 'debug.command', 'none')
            return
        if cmd == 'disable':
            try:
                print(f"[orchestrator][debug] consume cmd=disable", file=sys.stderr)
            except Exception:
                pass
            set_state_kv(db_path, worker, 'debug.enabled', 'false')
            set_state_kv(db_path, worker, 'debug.command', 'none')
            return
        if cmd == 'break_clear':
            set_state_kv(db_path, worker, 'debug.breakpoints', '[]')
            set_state_kv(db_path, worker, 'debug.command', 'none')
        time.sleep(0.05)
