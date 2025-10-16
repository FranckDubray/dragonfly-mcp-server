"""
Dynamic schema and metrics/last logs prompt sections built from the worker DB
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Tuple

SQLITE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "sqlite3"


def build_dynamic_schema_section(worker_id: str) -> str:
    db_path = _db_path_for_worker(worker_id)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
    cur = conn.cursor()

    def table_info(name: str) -> List[Tuple[str, str]]:
        try:
            cur.execute(f"PRAGMA table_info({name})")
            cols = [(row[1], row[2]) for row in cur.fetchall()]
            return cols
        except Exception:
            return []

    def table_count(name: str) -> int:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {name}")
            return int(cur.fetchone()[0] or 0)
        except Exception:
            return 0

    tables = ['job_steps', 'job_state_kv', 'job_meta']
    lines = ["INFOS RÉELLES (DB locale)\n"]
    for t in tables:
        cols = table_info(t)
        cnt = table_count(t)
        if cols:
            col_str = ", ".join([f"{c} {tp}" for c, tp in cols])
            lines.append(f"- Table {t} (≈ {cnt} lignes) : {col_str}")
        else:
            lines.append(f"- Table {t} : schéma indisponible")

    try:
        cur.execute("SELECT MAX(COALESCE(finished_at, started_at)) FROM job_steps")
        tmax = cur.fetchone()[0]
        if tmax:
            lines.append(f"- Dernier événement (job_steps): {tmax}")
    except Exception:
        pass

    conn.close()

    lines.append("\nRECOMMANDATIONS PRATIQUES\n- Utilise exclusivement les colonnes listées ci-dessus.\n- Pour grouper par statut ou filtrer par date, base-toi sur COALESCE(finished_at, started_at).\n- Évite les sous-requêtes lourdes; préfère LIMIT (20..100).\n- Pour obtenir le nœud courant, regarde job_state_kv (skeys: current_node, current_args).")

    return "\n".join(lines)


def build_process_data_section(worker_id: str) -> str:
    db_path = _db_path_for_worker(worker_id)
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
    cur = conn.cursor()

    def scalar(q: str) -> int:
        try:
            cur.execute(q)
            r = cur.fetchone()
            return int(r[0] or 0)
        except Exception:
            return 0

    # now/tmax pour fenêtre glissante 1h + statut
    now = scalar("SELECT strftime('%s','now')")
    tmax = scalar("SELECT MAX(strftime('%s', COALESCE(finished_at, started_at))) FROM job_steps")
    window_start = max(0, tmax - 3600) if tmax else 0
    age = (now - tmax) if (now and tmax) else 0
    status = 'running' if (age <= 300 and tmax) else 'idle'
    recent_failed = scalar("SELECT COUNT(*) FROM job_steps WHERE status='failed' AND strftime('%s', COALESCE(finished_at, started_at)) >= strftime('%s','now') - 900")

    total = scalar("SELECT COUNT(*) FROM job_steps")
    last_hour = scalar(f"SELECT COUNT(*) FROM job_steps WHERE strftime('%s', COALESCE(finished_at, started_at)) >= {window_start}") if window_start else 0
    succeeded = scalar("SELECT COUNT(*) FROM job_steps WHERE status='succeeded'")
    failed = scalar("SELECT COUNT(*) FROM job_steps WHERE status='failed'")
    llm_calls = scalar("SELECT COUNT(*) FROM job_steps WHERE name LIKE 'call_llm%' OR name LIKE 'call llm%'")
    cycles = scalar("SELECT COUNT(*) FROM job_steps WHERE name='sleep_interval'")
    if cycles == 0:
        cycles = scalar("SELECT COUNT(*) FROM job_steps WHERE name='finish_mailbox_db'")

    # Derniers 20 logs (sans args/result)
    logs: List[str] = []
    try:
        cur.execute("""
            SELECT id, name, status, COALESCE(finished_at, started_at) AS ts
            FROM job_steps
            ORDER BY id DESC
            LIMIT 20
        """)
        rows = cur.fetchall()
        for r in rows:
            rid, name, status_s, ts = r[0], str(r[1] or ''), str(r[2] or ''), str(r[3] or '')
            logs.append(f"- [{ts}] id={rid} name={name} status={status_s}")
    except Exception:
        pass
    finally:
        conn.close()

    lines = [
        "STATUT",
        f"- status: {status}",
        f"- last_event_age_sec: {age}",
        f"- recent_failed_15min: {recent_failed}",
        "",
        "MACROS (instantané DB)",
        f"- total_steps: {total}",
        f"- last_hour_steps: {last_hour}",
        f"- succeeded: {succeeded}",
        f"- failed: {failed}",
        f"- llm_calls: {llm_calls}",
        f"- cycles: {cycles}",
        "",
        "DERNIERS ÉVÉNEMENTS (20)",
        *logs,
    ]
    return "\n".join(lines)


def _db_path_for_worker(worker_id: str) -> Path:
    for pattern in [f"worker_{worker_id}.db", f"worker_{worker_id.capitalize()}.db"]:
        test_path = SQLITE_DIR / pattern
        if test_path.exists():
            return test_path
    raise FileNotFoundError(f"Worker {worker_id} not found in {SQLITE_DIR}")
