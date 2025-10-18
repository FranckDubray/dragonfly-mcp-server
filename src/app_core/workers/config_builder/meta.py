import sqlite3, json, os, logging
from typing import Any, Dict, Optional
from pathlib import Path
from .constants import SQLITE_DIR
logger = logging.getLogger(__name__)

def db_path_for_worker(worker_id: str) -> Path:
    # Debug: tracer le répertoire et les candidats
    try:
        logger.info(f"[CFG] SQLITE_DIR={SQLITE_DIR}")
    except Exception:
        pass
    last_candidate = None
    for pattern in [f"worker_{worker_id}.db", f"worker_{worker_id.capitalize()}.db"]:
        p = SQLITE_DIR / pattern
        last_candidate = p
        try:
            logger.info(f"[CFG] probing DB path: {p} exists={p.exists()}")
        except Exception:
            pass
        if p.exists():
            return p
    raise FileNotFoundError(f"Worker {worker_id} not found in {SQLITE_DIR} (last candidate: {last_candidate})")

def load_worker_meta(worker_id: str) -> dict:
    db_path = db_path_for_worker(worker_id)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
    cur = conn.cursor()
    cur.execute("SELECT skey, svalue FROM job_meta")
    rows = cur.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def get_meta_json(meta: dict, key: str, default=None):
    val = meta.get(key)
    if not val:
        return default
    try:
        return json.loads(val)
    except Exception:
        logger.warning(f"Invalid JSON in job_meta['{key}']")
        return default

def resolve_api_base(meta: Dict[str, Any]) -> str:
    api_base = str(meta.get('api_base') or '').rstrip('/')
    if api_base:
        return api_base
    endpoint = str(meta.get('llm_endpoint') or '').rstrip('/')
    if not endpoint:
        endpoint = os.getenv('LLM_ENDPOINT', '').rstrip('/')
    if not endpoint:
        return ''
    if "/chat/completions" in endpoint:
        return endpoint.replace("/chat/completions", "")
    elif "/api/v1/" in endpoint:
        return endpoint.split("/api/v1/")[0] + "/api/v1"
    elif endpoint.endswith("/api/v1"):
        return endpoint
    else:
        return endpoint
