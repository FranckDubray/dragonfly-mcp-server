"""
Sequencer minimal pour exécuter des séquences d'actions (timées) en arrière-plan.
- Un appel schedule() lance un thread court qui enchaîne les steps sans garder de WS ouvert.
- Stockage en mémoire uniquement; pas de side-effects à l'import.
- API: schedule(steps, note?) -> {script_id}; cancel(script_id) -> {cancelled}; get_status(script_id) -> dict.
"""
from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Dict, List, Optional

_SCRIPTS: Dict[str, Dict[str, Any]] = {}


def _now() -> float:
    return time.time()


def get_status(script_id: str) -> Dict[str, Any]:
    s = _SCRIPTS.get(script_id)
    if not s:
        return {"ok": False, "error": "not_found"}
    out = dict(s)
    out.pop("thread", None)
    return {"ok": True, **out}


def cancel(script_id: str) -> Dict[str, Any]:
    s = _SCRIPTS.get(script_id)
    if not s:
        return {"ok": False, "error": "not_found"}
    s["cancel"] = True
    return {"ok": True, "cancelled": True}


def schedule(steps: List[Dict[str, Any]], note: Optional[str] = None) -> Dict[str, Any]:
    if not isinstance(steps, list) or not steps:
        return {"ok": False, "error": "invalid_argument", "message": "steps requis (liste non vide)"}
    sid = str(uuid.uuid4())
    entry: Dict[str, Any] = {
        "id": sid,
        "note": note,
        "steps": steps,
        "started_at": None,
        "finished_at": None,
        "cancel": False,
        "status": "scheduled",
        "error": None,
    }
    _SCRIPTS[sid] = entry

    def _worker():
        from ..core import sequence as core_sequence  # import tardif
        entry["started_at"] = _now()
        entry["status"] = "running"
        try:
            core_sequence.run_steps(steps, cancel_flag=lambda: bool(_SCRIPTS.get(sid, {}).get("cancel")))
            entry["status"] = "succeeded" if not entry.get("cancel") else "cancelled"
        except Exception as e:  # noqa: BLE001
            entry["status"] = "failed"
            entry["error"] = type(e).__name__
        finally:
            entry["finished_at"] = _now()

    t = threading.Thread(target=_worker, daemon=True)
    entry["thread"] = t
    t.start()
    return {"ok": True, "script_id": sid, "scheduled": True}
