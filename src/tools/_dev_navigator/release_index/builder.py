"""
Dev Navigator Release Index Builder (implémentation Python v1)
- Mode offline, lecture seule du repo, aucune dépendance réseau
- Produit: ./sqlite3/<repo_slug>/<tag>__<shortsha>/index.db + manifest.json
- Parcours Python minimal: symbols, calls, imports, endpoints (FastAPI/Flask/Django) + dir_stats
"""
from __future__ import annotations
import os, json, time, sqlite3, hashlib
from typing import Dict, Any, Tuple, List

from .reader_paths import make_repo_slug
from .writer import insert_file, bulk_insert_symbols, bulk_link_container_symbols, bulk_insert_calls, bulk_insert_imports, bulk_insert_endpoints, upsert_dir_stats
from .extract_python import extract_symbols_calls_imports
from ..services.fs_scanner import is_binary_filename
from ..connectors.python.endpoints_fastapi import extract_endpoints as fe_fastapi
from ..connectors.python.endpoints_flask import extract_endpoints as fe_flask
from ..connectors.python.endpoints_django import extract_endpoints as fe_django

SCHEMA_VERSION = "1"
CONNECTOR_API_VERSION = "1"


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _ddl(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.executescript(
        """
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        PRAGMA foreign_keys=ON;

        CREATE TABLE IF NOT EXISTS files (
          id INTEGER PRIMARY KEY,
          relpath TEXT NOT NULL,
          lang TEXT,
          size INTEGER,
          mtime INTEGER,
          content_hash TEXT NOT NULL,
          is_test INTEGER DEFAULT 0,
          is_generated INTEGER DEFAULT 0,
          is_binary INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_files_relpath ON files(relpath);
        CREATE INDEX IF NOT EXISTS idx_files_lang ON files(lang);

        CREATE TABLE IF NOT EXISTS symbols (
          id INTEGER PRIMARY KEY,
          file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
          name TEXT NOT NULL,
          fqname TEXT,
          symbol_key TEXT,
          kind TEXT NOT NULL,
          lang TEXT,
          start_line INTEGER, start_col INTEGER,
          end_line INTEGER, end_col INTEGER,
          signature TEXT,
          container_symbol_id INTEGER REFERENCES symbols(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_id);
        CREATE INDEX IF NOT EXISTS idx_symbols_key ON symbols(symbol_key);

        CREATE TABLE IF NOT EXISTS references_ (
          id INTEGER PRIMARY KEY,
          file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
          symbol_id INTEGER REFERENCES symbols(id) ON DELETE SET NULL,
          symbol_key TEXT,
          kind TEXT NOT NULL,
          start_line INTEGER, start_col INTEGER,
          end_line INTEGER, end_col INTEGER,
          snippet TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_refs_symbol ON references_(symbol_id);
        CREATE INDEX IF NOT EXISTS idx_refs_key ON references_(symbol_key);

        CREATE TABLE IF NOT EXISTS calls (
          id INTEGER PRIMARY KEY,
          file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
          callee_symbol_id INTEGER REFERENCES symbols(id) ON DELETE SET NULL,
          callee_key TEXT NOT NULL,
          caller_symbol_id INTEGER REFERENCES symbols(id) ON DELETE SET NULL,
          start_line INTEGER, start_col INTEGER,
          args_shape TEXT,
          is_test INTEGER DEFAULT 0,
          snippet TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_calls_callee ON calls(callee_symbol_id);
        CREATE INDEX IF NOT EXISTS idx_calls_ckey ON calls(callee_key);
        CREATE INDEX IF NOT EXISTS idx_calls_caller ON calls(caller_symbol_id);

        CREATE TABLE IF NOT EXISTS imports (
          id INTEGER PRIMARY KEY,
          from_file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
          to_file_id INTEGER REFERENCES files(id) ON DELETE SET NULL,
          to_key TEXT,
          kind TEXT,
          raw TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_imports_from ON imports(from_file_id);
        CREATE INDEX IF NOT EXISTS idx_imports_to ON imports(to_file_id);

        CREATE TABLE IF NOT EXISTS endpoints (
          id INTEGER PRIMARY KEY,
          kind TEXT NOT NULL,
          method TEXT,
          path_or_name TEXT NOT NULL,
          source_file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
          source_line INTEGER NOT NULL,
          framework_hint TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_endpoints_kind ON endpoints(kind);

        CREATE TABLE IF NOT EXISTS dir_stats (
          id INTEGER PRIMARY KEY,
          dir_path TEXT NOT NULL,
          files INTEGER,
          bytes INTEGER
        );

        CREATE TABLE IF NOT EXISTS repo_metrics (
          id INTEGER PRIMARY KEY,
          metrics_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS errors (
          id INTEGER PRIMARY KEY,
          scope TEXT NOT NULL,
          code TEXT NOT NULL,
          message TEXT,
          created_at INTEGER DEFAULT (strftime('%s','now'))
        );
        """
    )
    cur.close()


def _hash_file(path: str) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_index(path: str, tag_name: str | None, commit_hash: str, analyzer_version: str,
                config_fingerprint: str, budgets: Dict[str, Any]) -> Tuple[str, str]:
    repo_slug = make_repo_slug(path)
    shortsha = commit_hash[:8]
    release_dir = os.path.join("sqlite3", repo_slug, f"{tag_name or 'no-tag'}__{shortsha}")
    os.makedirs(release_dir, exist_ok=True)
    db_path = os.path.join(release_dir, "index.db")

    conn = sqlite3.connect(db_path)
    try:
        _ddl(conn)
        cur = conn.cursor()

        # Accumulate dir stats
        dir_counters: Dict[str, Dict[str, int]] = {}

        # Scan repo under budgets (simplifié: sans .gitignore ici, car offline builder; à aligner si besoin)
        max_files = int(budgets.get("max_files_scanned", 10000))
        scanned = 0
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'vendor', 'dist', 'build', '.venv', '.mypy_cache', '.pytest_cache', '.cache', 'target', 'coverage', '__pycache__', 'snapshots'}]
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, path)
                if rel.startswith(".git/"):
                    continue
                if is_binary_filename(fn):
                    continue
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                file_id = insert_file(cur, rel, int(st.st_size), int(st.st_mtime), _hash_file(full), is_binary=0, is_test=1 if '/tests/' in rel or rel.startswith('tests/') else 0)

                # Python extraction
                if rel.endswith('.py'):
                    try:
                        with open(full, 'r', encoding='utf-8', errors='replace') as f:
                            code = f.read(min(int(budgets.get('max_bytes_per_file', 65536)), 1_048_576))
                    except Exception:
                        code = ""
                    facts = extract_symbols_calls_imports(code, rel)
                    ids = bulk_insert_symbols(cur, file_id, facts['symbols'])
                    bulk_link_container_symbols(cur, file_id, facts['symbols'], ids)
                    bulk_insert_calls(cur, file_id, facts['calls'], facts['symbols'], ids)

                    # Endpoints (FastAPI/Flask/Django)
                    eps: List[Dict[str, Any]] = []
                    eps.extend(fe_fastapi(code, rel))
                    eps.extend(fe_flask(code, rel))
                    if os.path.basename(rel) == 'urls.py':
                        eps.extend(fe_django(code, rel))
                    bulk_insert_endpoints(cur, file_id, eps)

                # Imports (light)
                # Reparse python code just once above; if non-py, skip imports
                if rel.endswith('.py') and 'facts' in locals():
                    bulk_insert_imports(cur, file_id, facts['imports'])

                # dir_stats
                parts = rel.split(os.sep)
                for d in range(1, min(len(parts), 5) + 1):
                    dpath = os.sep.join(parts[:d])
                    st_d = dir_counters.setdefault(dpath, {'files': 0, 'bytes': 0})
                    st_d['files'] += 1
                    st_d['bytes'] += int(st.st_size)

                scanned += 1
                if scanned >= max_files:
                    break
            if scanned >= max_files:
                break

        upsert_dir_stats(cur, dir_counters)
        conn.commit()
    finally:
        conn.close()

    integrity_hash = _hash_file(db_path)
    manifest = {
        "repo_slug": repo_slug,
        "tag_name": tag_name,
        "commit_hash": commit_hash,
        "created_at": int(time.time()),
        "schema_version": SCHEMA_VERSION,
        "connector_api_version": CONNECTOR_API_VERSION,
        "analyzer_version": analyzer_version,
        "config_fingerprint": config_fingerprint,
        "integrity_hash": integrity_hash,
    }
    manifest_path = os.path.join(release_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))
    return db_path, manifest_path
