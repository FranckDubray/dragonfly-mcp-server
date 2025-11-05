from __future__ import annotations
from typing import Dict, Any, List, Optional
import sqlite3
import json
import time
import logging
import re
from pathlib import Path

# Leader chat (LLM + sqlite_db tool), conversation transient (AUCUNE persistance DB)
# Le prompt provient EXCLUSIVEMENT de l'identité (worker_identity.identity_json.prompt). Aucune autre consigne système n'est codée en dur.

logger = logging.getLogger(__name__)

# Limiter la sortie LLM pour le chat (pas de flood)
MAX_OUTPUT_TOKENS = 600

def _db_path(worker_name: str) -> str:
    from src.tools._py_orchestrator.api_spawn import db_path_for_worker
    return db_path_for_worker(worker_name)

def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", (s or "").lower()).strip("_")

async def post_message(worker_name: str, message: str, model: str = "gpt-5-mini", history_limit: int = 20) -> Dict[str, Any]:
    dbp = _db_path(worker_name)
    conn = sqlite3.connect(dbp, timeout=3.0)
    try:
        # Contexte en lecture seule pour aider le modèle (aucune directive système codée en dur)
        ctx: Dict[str, Any] = {"identity": {}, "status": {}, "recent_steps": []}
        identity_prompt = ""
        try:
            cur = conn.execute("SELECT identity_json FROM worker_identity WHERE worker_name=? LIMIT 1", (worker_name,))
            row = cur.fetchone()
            if row:
                idj = json.loads(row[0] or '{}')
                ctx["identity"] = idj
                identity_prompt = str(idj.get("prompt") or "").strip()
        except Exception:
            pass
        try:
            kv = {}
            cur = conn.execute("SELECT skey, svalue FROM job_state_kv WHERE worker <> ''")
            for sk, sv in cur.fetchall():
                kv[str(sk)] = sv
            ctx["status"] = kv
        except Exception:
            pass
        try:
            cur = conn.execute(
                "SELECT node, status, duration_ms, details_json, finished_at FROM job_steps ORDER BY rowid DESC LIMIT 10"
            )
            for node, st, dur, dj, fin in cur.fetchall():
                rec = {"node": node, "status": st, "duration_ms": int(dur or 0), "finished_at": fin}
                if dj:
                    try:
                        obj = json.loads(dj)
                        rec["out_preview"] = obj.get("last_result_preview")
                    except Exception:
                        pass
                ctx["recent_steps"].append(rec)
        except Exception:
            pass

        messages: List[Dict[str, Any]] = []
        # 1) Unique system prompt: identité (si présent)
        if identity_prompt:
            messages.append({"role": "system", "content": identity_prompt})
        # 2) Contexte en lecture seule (user)
        messages.append({"role": "user", "content": f"Contexte (lecture seule):\n{json.dumps(ctx, ensure_ascii=False)}"})
        # 3) Message utilisateur
        messages.append({"role": "user", "content": message})

        from src.tools._call_llm.core import execute_call_llm
        timeout_sec = 90
        llm_res = execute_call_llm(
            messages=messages,
            model=model,
            tool_names=["sqlite_db"],
            max_tokens=MAX_OUTPUT_TOKENS,
            debug=False,
            timeout_sec=timeout_sec,
        )

        err = llm_res.get("error") if isinstance(llm_res, dict) else None
        if err:
            return {"accepted": False, "status": "llm_error", "message": err}

        content = (llm_res.get("content") or "").strip()
        return {"accepted": True, "status": "ok", "content": content, "usage": llm_res.get("usage") or {}}
    finally:
        try:
            conn.close()
        except Exception:
            pass

async def get_history(worker_name: str, limit: int = 30) -> Dict[str, Any]:
    # Historique désactivé
    return {"accepted": True, "status": "ok", "history": []}
