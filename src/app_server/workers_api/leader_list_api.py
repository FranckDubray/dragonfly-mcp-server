























from __future__ import annotations
from typing import Dict, Any, List
import sqlite3
from pathlib import Path

async def list_leaders() -> Dict[str, Any]:
    # Scan sqlite dir for leader_*.db and read leader_identity
    try:
        from src.tools._py_orchestrator.api_common import SQLITE_DIR
    except Exception:
        # Fallback path
        from pathlib import Path as _P
        SQLITE_DIR = _P.cwd() / 'sqlite3'
    items: List[Dict[str, Any]] = []
    base = Path(SQLITE_DIR)
    for dbp in sorted(base.glob('leader_*.db')):
        try:
            conn = sqlite3.connect(str(dbp), timeout=2.0)
            try:
                cur = conn.execute("SELECT leader_name, identity_json FROM leader_identity LIMIT 1")
                row = cur.fetchone()
                if not row: 
                    continue
                name, identity_json = row
                import json
                ident = {}
                try:
                    ident = json.loads(identity_json or '{}')
                except Exception:
                    ident = {}
                items.append({"name": name, "identity": ident})
            finally:
                conn.close()
        except Exception:
            continue
    return {"accepted": True, "status": "ok", "leaders": items}
