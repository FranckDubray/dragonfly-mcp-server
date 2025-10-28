"""
Waiters/polling pour états finaux (stream actif, transition terminée, media fini).
- Polling léger (200–500ms), timeouts par action.
- Pas d'I/O à l'import.
"""
from __future__ import annotations

import time
from typing import Callable, Any, Dict


def wait_until(predicate: Callable[[], Dict[str, Any]], timeout_sec: int, interval_sec: float = 0.3) -> Dict[str, Any]:
    start = time.time()
    while True:
        state = predicate()
        if state.get("ok") and state.get("done"):
            return state
        if time.time() - start > timeout_sec:
            return {"ok": False, "error": "timeout"}
        time.sleep(interval_sec)
