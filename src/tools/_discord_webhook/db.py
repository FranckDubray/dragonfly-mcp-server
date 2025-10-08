from __future__ import annotations
import os, json, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

# Robust project root detection (no relative import to config)

def _find_project_root() -> Path:
    cur = Path(__file__).resolve()
    # Walk up until we find a marker (pyproject.toml, .git) or a folder that contains 'src'
    for _ in range(8):  # limit ascent to avoid runaway
        if (cur / 'pyproject.toml').exists() or (cur / '.git').exists():
            return cur
        # Heuristic: if current folder contains 'src' directory, assume it's the project root
        if (cur / 'src').exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    # Fallback: current working directory
    return Path.cwd()

PROJECT_ROOT = _find_project_root()
DB_PATH = os.path.join(str(PROJECT_ROOT), "sqlite3", "discord_posts.db")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
              article_key TEXT PRIMARY KEY,
              webhook_hash TEXT NOT NULL,
              message_ids_json TEXT NOT NULL,
              embeds_counts_json TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


@contextmanager
def db_conn():
    ensure_db()
    conn = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        yield conn
    finally:
        conn.close()


def db_get(conn: sqlite3.Connection, article_key: str) -> Optional[Dict[str, Any]]:
    cur = conn.execute(
        "SELECT article_key, webhook_hash, message_ids_json, embeds_counts_json, created_at, updated_at FROM posts WHERE article_key = ?",
        (article_key,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "article_key": row[0],
        "webhook_hash": row[1],
        "message_ids": json.loads(row[2]),
        "embeds_counts": json.loads(row[3]),
        "created_at": row[4],
        "updated_at": row[5],
    }


def db_list(conn: sqlite3.Connection):
    cur = conn.execute("SELECT article_key, message_ids_json, updated_at FROM posts ORDER BY updated_at DESC")
    out = []
    for ak, mids_json, updated_at in cur.fetchall():
        out.append({"article_key": ak, "message_count": len(json.loads(mids_json)), "updated_at": updated_at})
    return out


def db_create(conn: sqlite3.Connection, article_key: str, wh_hash: str, message_ids: List[str], embeds_counts: List[int]):
    now = now_iso()
    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.execute("SELECT 1 FROM posts WHERE article_key = ?", (article_key,))
        if cur.fetchone():
            raise ValueError("exists")
        conn.execute(
            "INSERT INTO posts(article_key, webhook_hash, message_ids_json, embeds_counts_json, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (article_key, wh_hash, json.dumps(message_ids), json.dumps(embeds_counts), now, now),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def db_update(conn: sqlite3.Connection, article_key: str, wh_hash: str, message_ids: List[str], embeds_counts: List[int]):
    now = now_iso()
    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.execute("SELECT 1 FROM posts WHERE article_key = ?", (article_key,))
        if not cur.fetchone():
            raise ValueError("missing")
        conn.execute(
            "UPDATE posts SET webhook_hash = ?, message_ids_json = ?, embeds_counts_json = ?, updated_at = ? WHERE article_key = ?",
            (wh_hash, json.dumps(message_ids), json.dumps(embeds_counts), now, article_key),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def db_delete(conn: sqlite3.Connection, article_key: str) -> int:
    conn.execute("BEGIN IMMEDIATE")
    try:
        cur = conn.execute("DELETE FROM posts WHERE article_key = ?", (article_key,))
        deleted = cur.rowcount or 0
        conn.commit()
        return deleted
    except Exception:
        conn.rollback()
        raise
