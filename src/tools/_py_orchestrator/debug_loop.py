
from __future__ import annotations
import time
from .db import get_state_kv, set_state_kv

# Minimal debug wait loop compatible with KV protocol used by runner
# Waits until a movement command is processed and a pause is requested or cleared

def debug_wait_loop(db_path: str, worker: str, tick: float = 0.2, timeout: float | None = None):
    start = time.time()
    while True:
        # Exit on cancel or terminal phase
        try:
            phase = get_state_kv(db_path, worker, 'phase') or ''
            if phase in {'completed','failed','canceled'}:
                return
        except Exception:
            pass
        # If pause requested is cleared, we can break
        try:
            pr = get_state_kv(db_path, worker, 'debug.pause_request') or ''
            if not pr:
                return
        except Exception:
            pass
        if timeout is not None and (time.time() - start) > timeout:
            return
        time.sleep(tick)
