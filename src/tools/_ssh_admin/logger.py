"""
Audit logging for SSH operations.
"""
from __future__ import annotations
import sqlite3
import os
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from .utils import get_project_root
except Exception:
    from src.tools._ssh_admin.utils import get_project_root

def get_audit_db_path() -> Path:
    """Get path to audit database."""
    project_root = get_project_root()
    db_dir = project_root / "sqlite3"
    db_dir.mkdir(exist_ok=True)
    return db_dir / "ssh_audit.db"

def ensure_audit_db():
    """Create audit database if not exists."""
    db_path = get_audit_db_path()
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ssh_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                profile TEXT NOT NULL,
                operation TEXT NOT NULL,
                command TEXT,
                remote_path TEXT,
                local_path TEXT,
                exit_code INTEGER,
                success BOOLEAN NOT NULL,
                duration_ms INTEGER NOT NULL,
                output_size_bytes INTEGER,
                error_message TEXT,
                user TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indexes for fast queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON ssh_audit(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_profile ON ssh_audit(profile)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_operation ON ssh_audit(operation)")
        
        conn.commit()

@contextmanager
def audit_db():
    """Context manager for audit database."""
    ensure_audit_db()
    db_path = get_audit_db_path()
    conn = sqlite3.connect(str(db_path), timeout=10, isolation_level=None)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        yield conn
    finally:
        conn.close()

def log_ssh_operation(
    profile: str,
    operation: str,
    duration_ms: int,
    success: bool,
    command: Optional[str] = None,
    remote_path: Optional[str] = None,
    local_path: Optional[str] = None,
    exit_code: Optional[int] = None,
    output_size_bytes: Optional[int] = None,
    error_message: Optional[str] = None
):
    """Log SSH operation to audit database."""
    timestamp = datetime.now(timezone.utc).isoformat()
    user = os.getenv("USER") or os.getenv("USERNAME") or "unknown"
    
    with audit_db() as conn:
        conn.execute("""
            INSERT INTO ssh_audit (
                timestamp, profile, operation, command, remote_path, local_path,
                exit_code, success, duration_ms, output_size_bytes, error_message, user
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, profile, operation, command, remote_path, local_path,
            exit_code, success, duration_ms, output_size_bytes, error_message, user
        ))
