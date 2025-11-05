
from __future__ import annotations
from typing import Optional
from .utils.time import utcnow_str


def ensure_identity(db_path: str, worker_name: str, template: str, first_name: str, leader: Optional[str] = None) -> None:
    import sqlite3, json
    try:
        conn = sqlite3.connect(db_path, timeout=3.0)
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
            identity = {
                'display_name': first_name,
                'template': template,
                'role': f"Worker — {template}",
                'mission': f"Process template {template}",
                'status': 'En veille',
                'spm': 0,
                'tools': [],
                'avatar_url': '',
                'kv': {},
            }
            if leader:
                identity['leader'] = leader
            conn.execute(
                "INSERT INTO worker_identity(worker_name, template, first_name, identity_json, created_at, leader_name) VALUES(?,?,?,?,?,?)\n"
                "ON CONFLICT(worker_name) DO UPDATE SET template=excluded.template, first_name=excluded.first_name, identity_json=excluded.identity_json, leader_name=excluded.leader_name",
                (worker_name, template, first_name, json.dumps(identity, ensure_ascii=False), utcnow_str(), leader or '')
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def ensure_leader_db(leader_name: str) -> None:
    try:
        from .api_common import SQLITE_DIR
        from .start_helpers import slugify
        import sqlite3, json
        SQLITE_DIR.mkdir(parents=True, exist_ok=True)
        slug = slugify(leader_name)
        dbp = (SQLITE_DIR / f"leader_{slug}.db").as_posix()
        conn = sqlite3.connect(dbp, timeout=3.0)
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS leader_identity (\n"
                "  leader_name TEXT PRIMARY KEY,\n"
                "  identity_json TEXT,\n"
                "  created_at TEXT\n"
                ")"
            )
            ident = {
                'display_name': leader_name,
                'role': 'Leader',
                'persona': 'Orchestrateur des workers',
                'avatar_url': '',
                'kv': {},
            }
            conn.execute(
                "INSERT INTO leader_identity(leader_name, identity_json, created_at) VALUES(?,?,?)\n"
                "ON CONFLICT(leader_name) DO UPDATE SET identity_json=excluded.identity_json",
                (slug, json.dumps(ident, ensure_ascii=False), utcnow_str())
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass
