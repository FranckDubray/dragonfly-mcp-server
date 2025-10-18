import os
import sqlite3
import json as _json
import time as _time
import datetime as _dt
from typing import Optional as _Optional, Dict as _Dict, Any as _Any

# ---------- Time utils ----------

def utcnow_str() -> str:
    # Seconds precision (kept for heartbeat/ts compatibility)
    return _dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

def _utcnow_str_ms() -> str:
    # Microseconds for stable ordering of job_steps started_at/finished_at
    return _dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')

# ---------- DB path / schema ----------

_DEF_SQLITE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'sqlite3'))

SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS job_meta (
  skey TEXT PRIMARY KEY,
  svalue TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_state_kv (
  mailbox TEXT NOT NULL,
  skey TEXT NOT NULL,
  svalue TEXT,
  PRIMARY KEY (mailbox, skey)
);

CREATE TABLE IF NOT EXISTS job_steps (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mailbox TEXT NOT NULL,
  step_key TEXT NOT NULL,
  name TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('running','succeeded','failed','skipped')),
  started_at TEXT,
  finished_at TEXT,
  duration_ms INTEGER,
  details_json TEXT
);

CREATE TABLE IF NOT EXISTS mail_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mailbox TEXT NOT NULL,
  folder TEXT NOT NULL,
  uid TEXT NOT NULL,
  from_addr TEXT,
  subject TEXT,
  date_hdr TEXT,
  snippet TEXT,
  body_len INTEGER,
  truncated INTEGER DEFAULT 0,
  body_hash TEXT,
  UNIQUE(mailbox, folder, uid)
);

CREATE TABLE IF NOT EXISTS mail_classifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mailbox TEXT NOT NULL,
  folder TEXT NOT NULL,
  uid TEXT NOT NULL,
  class TEXT NOT NULL,
  urgency TEXT,
  intent TEXT,
  hints TEXT,
  entities_json TEXT,
  truncated INTEGER DEFAULT 0,
  body_chars INTEGER,
  model TEXT,
  ts TEXT NOT NULL,
  score INTEGER,
  UNIQUE(mailbox, folder, uid)
);

CREATE TABLE IF NOT EXISTS mail_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mailbox TEXT NOT NULL,
  folder TEXT NOT NULL,
  uid TEXT NOT NULL,
  action TEXT NOT NULL CHECK(action IN ('mark_read','move_spam')),
  ts TEXT NOT NULL,
  UNIQUE(mailbox, folder, uid, action)
);

CREATE TABLE IF NOT EXISTS llm_usage (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mailbox TEXT NOT NULL,
  folder TEXT NOT NULL,
  uid TEXT NOT NULL,
  model TEXT NOT NULL,
  tokens_input INTEGER NOT NULL,
  tokens_output INTEGER NOT NULL,
  ts TEXT NOT NULL,
  UNIQUE(mailbox, folder, uid, model)
);
"""


def _ensure_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def _ensure_schema(db_path: str) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.executescript(SCHEMA_DDL)
        con.commit()
    finally:
        con.close()


def get_db_path(worker_name: str) -> str:
    name = (worker_name or 'default').strip() or 'default'
    safe = ''.join(ch for ch in name if ch.isalnum() or ch in ('-', '_'))
    db_path = os.path.join(_DEF_SQLITE_DIR, f'worker_{safe}.db')
    _ensure_dir(_DEF_SQLITE_DIR)
    if not os.path.exists(db_path):
        _ensure_schema(db_path)
    return db_path

# ---------- job_meta helpers ----------

def set_meta(db_path: str, skey: str, svalue: str) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            "INSERT OR REPLACE INTO job_meta(skey, svalue) VALUES(?,?)",
            (skey, svalue),
        )
        con.commit()
    finally:
        con.close()


def get_meta(db_path: str, skey: str) -> _Optional[str]:
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(
            "SELECT svalue FROM job_meta WHERE skey=?",
            (skey,),
        )
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        con.close()

# ---------- state kv ----------

def set_state_kv(db_path: str, mailbox: str, skey: str, svalue: str) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            "INSERT OR REPLACE INTO job_state_kv(mailbox, skey, svalue) VALUES(?,?,?)",
            (mailbox, skey, svalue),
        )
        con.commit()
    finally:
        con.close()


def get_state_kv(db_path: str, mailbox: str, skey: str) -> _Optional[str]:
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(
            "SELECT svalue FROM job_state_kv WHERE mailbox=? AND skey=?",
            (mailbox, skey),
        )
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        con.close()

# ---------- steps ----------

def begin_step(db_path: str, mailbox: str, step_key: str, name: str, details: _Dict[str, _Any] | None = None) -> None:
    started_at = _utcnow_str_ms()
    details_json = _json.dumps(details or {}, ensure_ascii=False)
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO job_steps(mailbox, step_key, name, status, started_at, finished_at, duration_ms, details_json)
            VALUES(?,?,?,?,?,NULL,NULL,?)
            """,
            (mailbox, step_key, name, 'running', started_at, details_json),
        )
        con.commit()
    finally:
        con.close()


def end_step(db_path: str, mailbox: str, step_key: str, name: str, status: str, started_ts: float, details: _Dict[str, _Any] | None = None) -> None:
    finished_at = _utcnow_str_ms()
    try:
        duration_ms = int(max(0, (_time.time() - float(started_ts)) * 1000))
    except Exception:
        duration_ms = None
    details_json = _json.dumps(details or {}, ensure_ascii=False)

    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(
            "SELECT id FROM job_steps WHERE mailbox=? AND step_key=? AND name=? ORDER BY id DESC LIMIT 1",
            (mailbox, step_key, name),
        )
        row = cur.fetchone()
        if row:
            step_id = row[0]
            con.execute(
                """
                UPDATE job_steps
                SET status=?, finished_at=?, duration_ms=?, details_json=?
                WHERE id=?
                """,
                (status, finished_at, duration_ms, details_json, step_id),
            )
            con.commit()
        else:
            con.execute(
                """
                INSERT INTO job_steps(mailbox, step_key, name, status, started_at, finished_at, duration_ms, details_json)
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (mailbox, step_key, name, status, finished_at, finished_at, duration_ms, details_json),
            )
            con.commit()
    finally:
        con.close()

# ---------- domain inserts ----------

def upsert_mail_message(
    db_path: str,
    mailbox: str,
    folder: str,
    uid: str,
    from_addr: str | None,
    subject: str | None,
    date_hdr: str | None,
    snippet: str | None,
    body_len: int | None,
    truncated: bool | int | None,
    body_hash: str | None,
) -> None:
    tval = 1 if truncated else 0
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO mail_messages(mailbox, folder, uid, from_addr, subject, date_hdr, snippet, body_len, truncated, body_hash)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(mailbox, folder, uid) DO UPDATE SET
              from_addr=excluded.from_addr,
              subject=excluded.subject,
              date_hdr=excluded.date_hdr,
              snippet=excluded.snippet,
              body_len=excluded.body_len,
              truncated=excluded.truncated,
              body_hash=excluded.body_hash
            """,
            (mailbox, folder, uid, from_addr, subject, date_hdr, snippet, body_len, tval, body_hash),
        )
        con.commit()
    finally:
        con.close()


def insert_classification(
    db_path: str,
    mailbox: str,
    folder: str,
    uid: str,
    klass: str,
    score: int,
    urgency: str | None,
    intent: str | None,
    hints: str | None,
    entities: _Dict[str, _Any] | None,
    truncated: bool | int | None,
    body_chars: int | None,
    model: str | None,
) -> None:
    tval = 1 if truncated else 0
    entities_json = _json.dumps(entities or {}, ensure_ascii=False)
    ts = utcnow_str()
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO mail_classifications(mailbox, folder, uid, class, score, urgency, intent, hints, entities_json, truncated, body_chars, model, ts)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(mailbox, folder, uid) DO UPDATE SET
              class=excluded.class,
              score=excluded.score,
              urgency=excluded.urgency,
              intent=excluded.intent,
              hints=excluded.hints,
              entities_json=excluded.entities_json,
              truncated=excluded.truncated,
              body_chars=excluded.body_chars,
              model=excluded.model,
              ts=excluded.ts
            """,
            (mailbox, folder, uid, klass, score, urgency, intent, hints, entities_json, tval, body_chars, model, ts),
        )
        con.commit()
    finally:
        con.close()


def insert_action(db_path: str, mailbox: str, folder: str, uid: str, action: str) -> None:
    ts = utcnow_str()
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT OR IGNORE INTO mail_actions(mailbox, folder, uid, action, ts)
            VALUES(?,?,?,?,?)
            """,
            (mailbox, folder, uid, action, ts),
        )
        con.commit()
    finally:
        con.close()


def insert_llm_usage(
    db_path: str,
    mailbox: str,
    folder: str,
    uid: str,
    model: str,
    tokens_input: int,
    tokens_output: int,
) -> None:
    ts = utcnow_str()
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            INSERT INTO llm_usage(mailbox, folder, uid, model, tokens_input, tokens_output, ts)
            VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(mailbox, folder, uid, model) DO UPDATE SET
              tokens_input=excluded.tokens_input,
              tokens_output=excluded.tokens_output,
              ts=excluded.ts
            """,
            (mailbox, folder, uid, model, int(tokens_input or 0), int(tokens_output or 0), ts),
        )
        con.commit()
    finally:
        con.close()
