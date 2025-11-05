
from __future__ import annotations
from typing import Dict, Any
import sqlite3
import json
import os
from pathlib import Path

# Leader identity is stored in a dedicated DB: sqlite3/leader_<slug>.db (table leader_identity)

def _slugify(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9_]+", "_", (s or "").lower()).strip("_")

def _leader_db_path(leader_name: str) -> str:
    from src.tools._py_orchestrator.api_common import SQLITE_DIR
    slug = _slugify(leader_name)
    return str((Path(SQLITE_DIR) / f"leader_{slug}.db").resolve())

async def get_identity(name: str) -> Dict[str, Any]:
    dbp = _leader_db_path(name)
    conn = sqlite3.connect(dbp, timeout=3.0)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS leader_identity (\n"
            "  leader_name TEXT PRIMARY KEY,\n"
            "  identity_json TEXT,\n"
            "  created_at TEXT\n"
            ")"
        )
        cur = conn.execute("SELECT leader_name, identity_json FROM leader_identity WHERE leader_name=? LIMIT 1", (_slugify(name),))
        row = cur.fetchone()
        if not row:
            # Return empty identity gracefully (UI can edit)
            return {"accepted": True, "status": "empty", "leader": _slugify(name), "identity": {}}
        leader_name, identity_json = row
        ident = {}
        try:
            ident = json.loads(identity_json or '{}')
        except Exception:
            ident = {}
        return {"accepted": True, "status": "ok", "leader": leader_name, "identity": ident}
    finally:
        try: conn.close()
        except Exception: pass

# Propagate leader slug change to all workers leader_name and identity_json.leader
def _propagate_leader_rename(old_slug: str, new_slug: str) -> None:
    try:
        from src.tools._py_orchestrator.api_common import SQLITE_DIR
        base = Path(SQLITE_DIR)
        for dbp in sorted(base.glob("worker_*.db")):
            conn = sqlite3.connect(str(dbp), timeout=3.0)
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
                # Update rows with old_slug in leader_name
                cur = conn.execute(
                    "SELECT worker_name, identity_json FROM worker_identity WHERE COALESCE(leader_name,'')=?",
                    (old_slug,)
                )
                rows = cur.fetchall()
                for worker_name, identity_json in rows:
                    ident = {}
                    try: ident = json.loads(identity_json or '{}')
                    except Exception: ident = {}
                    if isinstance(ident, dict):
                        cur_leader = str(ident.get('leader') or '').strip()
                        if not cur_leader or cur_leader == old_slug:
                            ident['leader'] = new_slug
                    conn.execute(
                        "UPDATE worker_identity SET identity_json=?, leader_name=? WHERE worker_name=?",
                        (json.dumps(ident, ensure_ascii=False), new_slug, worker_name)
                    )
                # Also update identity_json.leader occurrences when leader_name is empty but JSON has old_slug
                cur = conn.execute("SELECT worker_name, identity_json, COALESCE(leader_name,'') FROM worker_identity")
                rows2 = cur.fetchall()
                for worker_name, identity_json, leader_name in rows2:
                    try: ident = json.loads(identity_json or '{}')
                    except Exception: ident = {}
                    if isinstance(ident, dict) and str(ident.get('leader') or '').strip() == old_slug:
                        ident['leader'] = new_slug
                        new_leader_col = new_slug if not leader_name else leader_name
                        conn.execute(
                            "UPDATE worker_identity SET identity_json=?, leader_name=? WHERE worker_name=?",
                            (json.dumps(ident, ensure_ascii=False), new_leader_col, worker_name)
                        )
                conn.commit()
            finally:
                try: conn.close()
                except Exception: pass
    except Exception:
        # best-effort
        pass

async def update_identity(name: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    old_slug = _slugify(name)
    dbp_old = _leader_db_path(name)
    Path(dbp_old).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(dbp_old, timeout=3.0)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS leader_identity (\n"
            "  leader_name TEXT PRIMARY KEY,\n"
            "  identity_json TEXT,\n"
            "  created_at TEXT\n"
            ")"
        )
        cur = conn.execute("SELECT leader_name, identity_json FROM leader_identity WHERE leader_name=? LIMIT 1", (old_slug,))
        row = cur.fetchone()
        if not row:
            # Create new leader identity
            ident = {}
            allowed = {"display_name", "persona", "avatar_url", "kv", "prompt"}
            for k, v in (patch or {}).items():
                if k in allowed:
                    ident[k] = v
            display = str(ident.get("display_name") or name).strip()
            new_slug = _slugify(display)
            conn.execute(
                "INSERT INTO leader_identity(leader_name, identity_json, created_at) VALUES(?,?,datetime('now'))",
                (new_slug, json.dumps(ident, ensure_ascii=False))
            )
            conn.commit()
            # If slug differs from provided name, consider propagate (no old attachments yet)
            if new_slug != old_slug:
                try: _propagate_leader_rename(old_slug, new_slug)
                except Exception: pass
            return {"accepted": True, "status": "ok", "leader": new_slug, "identity": ident}

        # Update existing
        leader_name, identity_json = row
        try:
            ident = json.loads(identity_json or '{}')
        except Exception:
            ident = {}
        allowed = {"display_name", "persona", "avatar_url", "kv", "prompt"}
        for k, v in (patch or {}).items():
            if k in allowed:
                ident[k] = v
        display = str(ident.get("display_name") or leader_name).strip()
        new_slug = _slugify(display)

        # If slug changes, rename DB file and propagate to workers
        if new_slug != leader_name:
            # Write into current DB first with new_slug row
            try:
                # upsert new row
                conn.execute(
                    "INSERT INTO leader_identity(leader_name, identity_json, created_at) VALUES(?,?,datetime('now'))\n"
                    "ON CONFLICT(leader_name) DO UPDATE SET identity_json=excluded.identity_json",
                    (new_slug, json.dumps(ident, ensure_ascii=False))
                )
                # remove old row if different key
                if new_slug != leader_name:
                    conn.execute("DELETE FROM leader_identity WHERE leader_name=?", (leader_name,))
                conn.commit()
            except Exception:
                pass
            # rename DB file if possible
            try:
                dbp_new = _leader_db_path(new_slug)
                if Path(dbp_old).exists():
                    if not Path(dbp_new).exists():
                        os.rename(dbp_old, dbp_new)
                    else:
                        # if target exists, keep old path but content updated
                        dbp_new = dbp_old
            except Exception:
                pass
            # propagate rename
            try:
                _propagate_leader_rename(leader_name, new_slug)
            except Exception:
                pass
            return {"accepted": True, "status": "ok", "leader": new_slug, "identity": ident}

        # No slug change; just update JSON
        conn.execute(
            "INSERT INTO leader_identity(leader_name, identity_json, created_at) VALUES(?,?,datetime('now'))\n"
            "ON CONFLICT(leader_name) DO UPDATE SET identity_json=excluded.identity_json",
            (leader_name, json.dumps(ident, ensure_ascii=False))
        )
        conn.commit()
        return {"accepted": True, "status": "ok", "leader": leader_name, "identity": ident}
    finally:
        try: conn.close()
        except Exception: pass
