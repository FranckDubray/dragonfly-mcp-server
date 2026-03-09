"""Local SQLite database for migration logs."""
from __future__ import annotations
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List

LOG = logging.getLogger(__name__)

# DB lives in <project>/sqlite3/assistant_migrations.db
_DB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "sqlite3"
_DB_PATH = _DB_DIR / "assistant_migrations.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS migrations (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    from_model_id INTEGER NOT NULL,
    from_model_name TEXT,
    to_model_id INTEGER NOT NULL,
    to_model_name TEXT,
    filters TEXT,
    affected_count INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'executed',
    rolled_back_at TEXT
);

CREATE TABLE IF NOT EXISTS migration_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_id TEXT NOT NULL,
    assistant_id INTEGER NOT NULL,
    assistant_name TEXT,
    old_model_ai_id INTEGER,
    new_model_ai_id INTEGER,
    FOREIGN KEY (migration_id) REFERENCES migrations(id)
);

CREATE INDEX IF NOT EXISTS idx_details_migration
    ON migration_details(migration_id);
"""


def _get_conn() -> sqlite3.Connection:
    """Get connection, create schema if needed."""
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def save_migration(
    migration_id: str,
    created_at: str,
    from_model_id: int,
    from_model_name: str,
    to_model_id: int,
    to_model_name: str,
    filters: str,
    affected_count: int,
    details: List[Dict[str, Any]],
) -> None:
    """Save a migration record + details."""
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO migrations VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                migration_id, created_at,
                from_model_id, from_model_name,
                to_model_id, to_model_name,
                filters, affected_count, "executed", None,
            ),
        )
        for d in details:
            conn.execute(
                "INSERT INTO migration_details "
                "(migration_id, assistant_id, assistant_name, "
                "old_model_ai_id, new_model_ai_id) VALUES (?,?,?,?,?)",
                (
                    migration_id, d["assistant_id"],
                    d["assistant_name"], d["old_model_ai_id"],
                    d["new_model_ai_id"],
                ),
            )
        conn.commit()
        LOG.info("💾 Migration %s saved (%d details)", migration_id, len(details))
    finally:
        conn.close()


def get_history(limit: int = 10, offset: int = 0) -> Dict[str, Any]:
    """Get migration history."""
    conn = _get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) FROM migrations").fetchone()[0]
        rows = conn.execute(
            "SELECT * FROM migrations ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return {
            "migrations": [dict(r) for r in rows],
            "returned_count": len(rows),
            "total_count": total,
            "has_more": (offset + len(rows)) < total,
        }
    finally:
        conn.close()


def get_migration_details(migration_id: str) -> List[Dict[str, Any]]:
    """Get details for a specific migration."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM migration_details WHERE migration_id = ?",
            (migration_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def mark_rolled_back(migration_id: str, rolled_back_at: str) -> bool:
    """Mark a migration as rolled back."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            "UPDATE migrations SET status = 'rolled_back', "
            "rolled_back_at = ? WHERE id = ? AND status = 'executed'",
            (rolled_back_at, migration_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
