







from __future__ import annotations
from typing import Dict, Any
import sqlite3
import json

# Read/Update worker identity (table worker_identity)

def _db_path(worker_name: str) -> str:
    from src.tools._py_orchestrator.api_spawn import db_path_for_worker
    return db_path_for_worker(worker_name)

async def get_identity(worker_name: str) -> Dict[str, Any]:
    dbp = _db_path(worker_name)
    conn = sqlite3.connect(dbp, timeout=3.0)
    try:
        # Ensure table exists
        conn.execute(
            "CREATE TABLE IF NOT EXISTS worker_identity (\n"
            "  worker_name TEXT PRIMARY KEY,\n"
            "  template TEXT,\n"
            "  first_name TEXT,\n"
            "  identity_json TEXT,\n"
            "  created_at TEXT,\n"
            "  leader_name TEXT\n"
            ")"
        )
        cur = conn.execute("SELECT template, first_name, identity_json, COALESCE(leader_name,'') FROM worker_identity WHERE worker_name=? LIMIT 1", (worker_name,))
        row = cur.fetchone()
        if not row:
            # Return empty identity gracefully (UI can edit)
            return {"accepted": True, "status": "empty", "template": "", "first_name": "", "identity": {}}
        template, first_name, identity_json, leader_name = row
        ident = {}
        try:
            ident = json.loads(identity_json or '{}')
        except Exception:
            ident = {}
        if leader_name and isinstance(ident, dict):
            ident.setdefault('leader', leader_name)
        return {"accepted": True, "status": "ok", "template": template or "", "first_name": first_name or "", "identity": ident}
    finally:
        try: conn.close()
        except Exception: pass

async def update_identity(worker_name: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    dbp = _db_path(worker_name)
    conn = sqlite3.connect(dbp, timeout=3.0)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS worker_identity (\n"
            "  worker_name TEXT PRIMARY KEY,\n"
            "  template TEXT,\n"
            "  first_name TEXT,\n"
            "  identity_json TEXT,\n"
            "  created_at TEXT,\n"
            "  leader_name TEXT\n"
            ")"
        )
        cur = conn.execute("SELECT template, first_name, identity_json, COALESCE(leader_name,'') FROM worker_identity WHERE worker_name=? LIMIT 1", (worker_name,))
        row = cur.fetchone()
        if not row:
            # Insert new identity
            ident = {}
            allowed = {"display_name", "persona", "role", "mission", "status", "spm", "tools", "avatar_url", "kv", "leader"}
            for k, v in (patch or {}).items():
                if k in allowed:
                    ident[k] = v
            first_name = patch.get("first_name") or patch.get("display_name") or ""
            leader_slug = str(ident.get('leader') or '').strip()
            # Persist leader_name column too when provided
            conn.execute(
                "INSERT INTO worker_identity(worker_name, template, first_name, identity_json, created_at, leader_name) VALUES(?,?,?,?,datetime('now'),?)",
                (worker_name, "", str(first_name or ""), json.dumps(ident, ensure_ascii=False), leader_slug)
            )
            conn.commit()
            # Best-effort: clear KV 'leader' to avoid stale duplicates
            try:
                from src.tools._py_orchestrator.db import set_state_kv
                set_state_kv(dbp, worker_name, 'leader', '')
            except Exception:
                pass
            return {"accepted": True, "status": "ok", "template": "", "first_name": str(first_name or ""), "identity": ident}
        template, first_name, identity_json, leader_name = row
        try:
            ident = json.loads(identity_json or '{}')
        except Exception:
            ident = {}
        # Merge shallow keys we allow from patch
        allowed = {"display_name", "persona", "role", "mission", "status", "spm", "tools", "avatar_url", "kv", "leader"}
        for k, v in (patch or {}).items():
            if k in allowed:
                ident[k] = v
            if k == "first_name":
                first_name = str(v or "")
        # Sync leader_name column with identity.leader if provided
        new_leader = str(ident.get('leader') or '').strip()
        conn.execute(
            "UPDATE worker_identity SET first_name=?, identity_json=?, leader_name=? WHERE worker_name=?",
            (first_name, json.dumps(ident, ensure_ascii=False), new_leader, worker_name)
        )
        conn.commit()
        # Best-effort: clear KV 'leader' to avoid stale duplicates
        try:
            from src.tools._py_orchestrator.db import set_state_kv
            set_state_kv(dbp, worker_name, 'leader', '')
        except Exception:
            pass
        return {"accepted": True, "status": "ok", "template": template or "", "first_name": first_name or "", "identity": ident}
    finally:
        try: conn.close()
        except Exception: pass
