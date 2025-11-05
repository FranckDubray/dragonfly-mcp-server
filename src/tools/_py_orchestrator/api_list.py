














# List workers (autonomous; no dependency on old JSON orchestrator)
from __future__ import annotations
from pathlib import Path
import sqlite3
from typing import List, Dict, Any

from .api_common import SQLITE_DIR


def _read_kv(conn: sqlite3.Connection, key: str, worker: str) -> str:
    try:
        cur = conn.execute(
            "SELECT svalue FROM job_state_kv WHERE worker=? AND skey=?",
            (worker, key),
        )
        row = cur.fetchone()
        return row[0] if row and row[0] is not None else ""
    except Exception:
        return ""


def _last_step_ts(conn: sqlite3.Connection, worker: str) -> str:
    try:
        cur = conn.execute(
            "SELECT COALESCE(finished_at, started_at) FROM job_steps WHERE worker=? ORDER BY rowid DESC LIMIT 1",
            (worker,),
        )
        row = cur.fetchone()
        return row[0] if row and row[0] is not None else ""
    except Exception:
        return ""


def _has_identity(conn: sqlite3.Connection, worker: str) -> bool:
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
        cur = conn.execute(
            "SELECT 1 FROM worker_identity WHERE worker_name=? LIMIT 1",
            (worker,),
        )
        return bool(cur.fetchone())
    except Exception:
        return False


def _is_real_worker(conn: sqlite3.Connection, worker: str) -> bool:
    """Filtre strict pour ignorer les DB fantômes.
    Un worker est 'réel' si:
      - job_steps a des lignes (au moins une exécution), OU
      - une identité existe dans worker_identity (ligne présente pour worker_name)
    On NE considère plus les KV (process_uid/worker_file) comme preuve de réalité.
    """
    try:
        cur = conn.execute("SELECT 1 FROM job_steps WHERE worker=? LIMIT 1", (worker,))
        if cur.fetchone():
            return True
    except Exception:
        pass
    return _has_identity(conn, worker)


def _read_identity(conn: sqlite3.Connection, worker: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"identity": {}, "leader": "", "first_name": ""}
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
        cur = conn.execute(
            "SELECT first_name, identity_json, COALESCE(leader_name,'') FROM worker_identity WHERE worker_name=? LIMIT 1",
            (worker,),
        )
        row = cur.fetchone()
        if not row:
            return out
        first_name, identity_json, leader_name = row
        import json
        ident = {}
        try:
            ident = json.loads(identity_json or '{}')
        except Exception:
            ident = {}
        out["identity"] = ident if isinstance(ident, dict) else {}
        out["leader"] = str(leader_name or "").strip()
        out["first_name"] = str(first_name or "").strip()
    except Exception:
        pass
    return out


def _tools_used(worker_name: str) -> List[str]:
    try:
        from .validators import PY_WORKERS_DIR
        from .controller_parts.graph_build import validate_and_extract_graph
        root = (Path(PY_WORKERS_DIR) / worker_name)
        if not root.exists():
            return []
        g = validate_and_extract_graph(root)
        tools = []
        seen = set()
        for n in g.get("nodes", []):
            if n.get("type") == "step" and n.get("call_kind") == "tool":
                tgt = str(n.get("call_target") or "").strip()
                if tgt and tgt not in seen:
                    seen.add(tgt); tools.append(tgt)
            if len(tools) >= 6:
                break
        return tools
    except Exception:
        return []


def list_workers() -> Dict[str, Any]:
    SQLITE_DIR.mkdir(parents=True, exist_ok=True)
    items: List[Dict[str, Any]] = []

    for dbp in sorted(Path(SQLITE_DIR).glob("worker_*.db")):
        try:
            worker_name = dbp.stem.replace("worker_", "", 1).strip()
            if not worker_name:
                continue
            conn = sqlite3.connect(str(dbp), timeout=2.0)
            try:
                # Filtrer les DB 'fantômes' strictement
                if not _is_real_worker(conn, worker_name):
                    continue
                phase = _read_kv(conn, "phase", worker_name) or "unknown"
                pid = _read_kv(conn, "pid", worker_name)
                hb = _read_kv(conn, "heartbeat", worker_name)
                process_uid = _read_kv(conn, "process_uid", worker_name)
                last_err = _read_kv(conn, "last_error", worker_name) or None
                last_step_at = _last_step_ts(conn, worker_name)
                ident_pack = _read_identity(conn, worker_name)
                # Single source of truth: worker_identity.leader_name only
                leader = ident_pack.get("leader") or ""
                identity = ident_pack.get("identity") or {}
                first_name = ident_pack.get("first_name") or ""
            finally:
                conn.close()
            items.append({
                "worker_name": worker_name,
                "status": phase or "unknown",
                "pid": (int(pid) if pid and pid.isdigit() else None),
                "heartbeat": hb,
                "last_step_at": last_step_at,
                "process_uid": process_uid or "",
                "process_version": "",
                "db_path": str(dbp.resolve()),
                "last_error": last_err,
                "leader": leader or "",
                "identity": identity,
                "first_name": first_name,
                "tools_used": _tools_used(worker_name),
            })
        except Exception:
            continue

    return {"accepted": True, "status": "ok", "workers": items}
