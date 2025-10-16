"""
Process (Mermaid) prompt section
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

SQLITE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "sqlite3"


def build_process_mermaid_section(worker_id: str) -> str:
    """Charge le diagramme Mermaid du process depuis la DB et l’explique pour le LLM."""
    db_path = _db_path_for_worker(worker_id)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
    cur = conn.cursor()

    mermaid = ''
    try:
        cur.execute("SELECT svalue FROM job_state_kv WHERE skey='graph_mermaid' ORDER BY rowid DESC LIMIT 1")
        row = cur.fetchone()
        if row and row[0]:
            mermaid = row[0]
        else:
            cur.execute("SELECT svalue FROM job_meta WHERE skey='graph_mermaid' LIMIT 1")
            row2 = cur.fetchone()
            if row2 and row2[0]:
                mermaid = row2[0]
    except Exception:
        pass
    finally:
        conn.close()

    if not mermaid:
        return (
            "PROCESSUS (Mermaid)\n"
            "- Les identifiants de nœuds correspondent à job_steps.name.\n"
            "- Le diagramme n’a pas été trouvé dans la DB."
        )

    return (
        "PROCESSUS (Mermaid)\n"
        "- Les identifiants de nœuds correspondent à job_steps.name.\n"
        "- Le diagramme décrit la logique d’orchestration; job_steps consigne les étapes réellement exécutées.\n\n"
        "```mermaid\n" + mermaid + "\n```"
    )


def _db_path_for_worker(worker_id: str) -> Path:
    for pattern in [f"worker_{worker_id}.db", f"worker_{worker_id.capitalize()}.db"]:
        test_path = SQLITE_DIR / pattern
        if test_path.exists():
            return test_path
    raise FileNotFoundError(f"Worker {worker_id} not found in {SQLITE_DIR}")
