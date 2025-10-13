from __future__ import annotations
import os, json, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

# Robust project root detection (no relative import to config)

def _find_project_root() -> Path:
    """
    Robust root detection that never falls back to CWD.
    Priority:
      1) Directory containing pyproject.toml or .git
      2) If inside 'src' (and 'tools' exists), return its parent
      3) Parent that contains a 'src' subfolder
      4) Heuristic: 3 levels up from this file (…/_discord_webhook -> tools -> src -> <repo>)
    """
    file_dir = Path(__file__).resolve().parent

    # 1) Explicit markers
    for cur in [file_dir, *file_dir.parents]:
        if (cur / 'pyproject.toml').exists() or (cur / '.git').exists():
            return cur

    # 2) If we're inside the 'src' directory of the project, go one up
    for cur in [file_dir, *file_dir.parents]:
        if cur.name == 'src' and (cur / 'tools').is_dir():
            return cur.parent

    # 3) Any parent that contains a 'src' directory
    for cur in [file_dir, *file_dir.parents]:
        if (cur / 'src').is_dir():
            return cur

    # 4) Safe heuristic: 3 levels up (…/repo)
    parents = list(file_dir.parents)
    return parents[2] if len(parents) >= 3 else parents[-1]

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
