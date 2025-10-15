import os, sqlite3, json, time, datetime as dt, re
from typing import Optional, Dict, Any

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

SAFE_NAME_RE = re.compile(r'[^a-zA-Z0-9_-]+')


def _db_path_for(worker_name: str) -> str:
    safe = SAFE_NAME_RE.sub('_', worker_name.strip())
    return os.path.join(ROOT_DIR, 'sqlite3', f'worker_{safe}.db')


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS job_state_kv (
  mailbox TEXT NOT NULL,
  skey TEXT NOT NULL,
  svalue TEXT,
  PRIMARY KEY(mailbox, skey)
);

CREATE TABLE IF NOT EXISTS job_meta (
  skey TEXT PRIMARY KEY,
  svalue TEXT
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
CREATE INDEX IF NOT EXISTS idx_steps_mailbox ON job_steps(mailbox);

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
CREATE INDEX IF NOT EXISTS idx_mm_mailbox ON mail_messages(mailbox);

CREATE TABLE IF NOT EXISTS mail_classifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mailbox TEXT NOT NULL,
  folder TEXT NOT NULL,
  uid TEXT NOT NULL,
  class TEXT NOT NULL,
  score INTEGER NOT NULL,
  urgency TEXT,
  intent TEXT,
  hints TEXT,
  entities_json TEXT,
  truncated INTEGER DEFAULT 0,
  body_chars INTEGER,
  model TEXT,
  ts TEXT NOT NULL,
  CHECK(score BETWEEN 1 AND 10),
  UNIQUE(mailbox, folder, uid)
);
CREATE INDEX IF NOT EXISTS idx_mc_mailbox ON mail_classifications(mailbox);

CREATE TABLE IF NOT EXISTS mail_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mailbox TEXT NOT NULL,
  folder TEXT NOT NULL,
  uid TEXT NOT NULL,
  action TEXT NOT NULL CHECK(action IN ('mark_read','move_spam')),
  ts TEXT NOT NULL,
  UNIQUE(mailbox, folder, uid, action)
);
CREATE INDEX IF NOT EXISTS idx_ma_mailbox ON mail_actions(mailbox);

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
CREATE INDEX IF NOT EXISTS idx_llm_mailbox ON llm_usage(mailbox);
"""


def ensure_db(worker_name: str) -> str:
    db = _db_path_for(worker_name)
    os.makedirs(os.path.join(ROOT_DIR, 'sqlite3'), exist_ok=True)
    con = sqlite3.connect(db)
    try:
        con.executescript(SCHEMA_SQL)
        con.commit()
    finally:
        con.close()
    return db


def get_db_path(worker_name: str) -> str:
    return ensure_db(worker_name)


def utcnow_str() -> str:
    return dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')


def set_meta(db_path: str, skey: str, svalue: str):
    con = sqlite3.connect(db_path)
    try:
        con.execute("INSERT OR REPLACE INTO job_meta(skey,svalue) VALUES(?,?)", (skey, svalue))
        con.commit()
    finally:
        con.close()


def get_meta(db_path: str, skey: str) -> Optional[str]:
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute("SELECT svalue FROM job_meta WHERE skey=?", (skey,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        con.close()

# ... le reste inchangé (state kv, steps, inserts, etc.)
