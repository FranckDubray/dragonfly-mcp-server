
from __future__ import annotations
from typing import Dict, Any, List, Optional
import sqlite3
import json
import time
from pathlib import Path
import logging

# Leader-level chat (transient: AUCUNE persistance).
# IMPORTANT: Aucun prompt système codé en dur; seul identity.prompt (leader) peut fournir un system.

def _slugify(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9_]+", "_", (s or "").lower()).strip("_")

def _leader_db_path(leader_name: str) -> str:
    from src.tools._py_orchestrator.api_common import SQLITE_DIR
    slug = _slugify(leader_name)
    return str((Path(SQLITE_DIR) / f"leader_{slug}.db").resolve())

# Plafond de génération
MAX_OUTPUT_TOKENS = 600
logger = logging.getLogger(__name__)

# Aucune persistance

def _ensure_tables(conn: sqlite3.Connection) -> None:
    return

def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def _load_history(conn: sqlite3.Connection, limit: int = 30) -> List[Dict[str, Any]]:
    return []

def _insert_msg(conn: sqlite3.Connection, role: str, content: str, meta: Optional[Dict[str, Any]] = None) -> None:
    return

async def post_message(leader_name: str, message: str, model: str = "gpt-5-mini", history_limit: int = 20) -> Dict[str, Any]:
    dbp = _leader_db_path(leader_name)
    conn = sqlite3.connect(dbp, timeout=3.0)
    try:
        _ensure_tables(conn)
        history = _load_history(conn, limit=history_limit)

        messages: List[Dict[str, Any]] = []
        # 1) Prompt d'identité leader (si présent) — pas d'autre system
        try:
            cur = conn.execute("SELECT identity_json FROM leader_identity WHERE leader_name=? LIMIT 1", (_slugify(leader_name),))
            row = cur.fetchone()
            if row and row[0]:
                ident = json.loads(row[0] or '{}')
                iprompt = str(ident.get("prompt") or "").strip()
                if iprompt:
                    messages.append({"role": "system", "content": iprompt})
        except Exception:
            pass

        # 2) Historique (si un jour activé) — non utilisé ici
        for h in []:
            messages.append({"role": h.get("role") or "assistant", "content": h.get("content") or ""})

        # 3) Message utilisateur (aucun contexte supplémentaire injecté)
        messages.append({"role": "user", "content": message})

        from src.tools._call_llm.core import execute_call_llm
        timeout_sec = 90
        logger.info("[leader_chat_global] llm call model=%s tools=%s timeout_sec=%s", model, ["sqlite_db"], timeout_sec)
        llm_res = execute_call_llm(messages=messages, model=model, tool_names=["sqlite_db"], max_tokens=MAX_OUTPUT_TOKENS, debug=False, timeout_sec=timeout_sec)

        err = llm_res.get("error") if isinstance(llm_res, dict) else None
        if err:
            return {"accepted": False, "status": "llm_error", "message": err}

        content = (llm_res.get("content") or "").strip()
        return {"accepted": True, "status": "ok", "content": content, "usage": llm_res.get("usage") or {}, "tools_preview": []}
    finally:
        try: conn.close()
        except Exception: pass

async def get_history(leader_name: str, limit: int = 30) -> Dict[str, Any]:
    return {"accepted": True, "status": "ok", "history": []}
