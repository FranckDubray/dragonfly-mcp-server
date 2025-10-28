"""
Gestion minimale de sessions courtes (TTL) pour obs_control.
- Pas de connexion WS persistante obligatoire: on conserve surtout un contexte (timeouts, notes).
- Une session est identifiée par un session_id (chaîne) et expire après TTL secondes.
- Aucune I/O à l'import. Stockage en mémoire de processus uniquement.
"""
from __future__ import annotations

import time
import uuid
from typing import Dict, Any, Optional

_SESSIONS: Dict[str, Dict[str, Any]] = {}

DEFAULT_SESSION_SEC = 30
MAX_SESSION_SEC = 60


def _now() -> float:
    return time.time()


def open_session(session_timeout_sec: Optional[int] = None, note: str | None = None) -> Dict[str, Any]:
    ttl = DEFAULT_SESSION_SEC if session_timeout_sec is None else int(session_timeout_sec)
    if ttl < 1:
        ttl = 1
    if ttl > MAX_SESSION_SEC:
        ttl = MAX_SESSION_SEC
    sid = str(uuid.uuid4())
    exp = _now() + ttl
    ctx = {
        "id": sid,
        "expires_at": exp,
        "note": note,
        "default_action_timeout_sec": None,
    }
    _SESSIONS[sid] = ctx
    return {"session_id": sid, "expires_in_sec": int(exp - _now())}


def close_session(session_id: str) -> Dict[str, Any]:
    if session_id in _SESSIONS:
        del _SESSIONS[session_id]
        return {"closed": True}
    return {"closed": False}


def get_session_ctx(session_id: Optional[str]) -> Dict[str, Any] | None:
    if not session_id:
        return None
    ctx = _SESSIONS.get(session_id)
    if not ctx:
        return None
    if ctx["expires_at"] <= _now():
        # Expirée
        try:
            del _SESSIONS[session_id]
        except Exception:
            pass
        return None
    return ctx
