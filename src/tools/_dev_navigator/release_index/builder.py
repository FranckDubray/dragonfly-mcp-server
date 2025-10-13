"""
Dev Navigator Release Index Builder (squelette)
- Mode offline, lecture seule du repo, aucune dépendance réseau
- Produit: ./sqlite3/<repo_slug>/<tag>__<shortsha>/index.db + manifest.json
- Schéma: tables (files, symbols, references_, calls, imports, endpoints, dir_stats, repo_metrics, errors)

Entrées (exemples):
- path: racine du repo
- tag_name: str (optionnel)
- commit_hash: str (obligatoire)
- analyzer_version: str
- config_fingerprint: str (hash des options/ignores/budgets)
- budgets: {max_files_scanned, max_bytes_per_file, ...}

Sorties:
- index.db (VACUUM, read-only at runtime)
- manifest.json {repo_slug, tag_name, commit_hash, created_at, schema_version, connector_api_version, counts, integrity_hash}

Remarque: ce squelette expose la structure et les étapes; l'impl détaillée d'extraction (symbols/refs/calls) pourra réutiliser les connecteurs existants.
"""
from __future__ import annotations
import os, json, time, sqlite3, hashlib
from typing import Dict, Any, Tuple

from .reader_paths import make_repo_slug

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
    """Build index under ./sqlite3/<repo_slug>/<tag>__<shortsha>/ and return (db_path, manifest_path)."""
    repo_slug = make_repo_slug(path)
    shortsha = commit_hash[:8]
    release_dir = os.path.join("sqlite3", repo_slug, f"{tag_name or 'no-tag'}__{shortsha}")
    _ensure_dir(release_dir)
    db_path = os.path.join(release_dir, "index.db")

    # Create DB and schema
    conn = sqlite3.connect(db_path)
    try:
        _ddl(conn)
        # TODO: scan files with budgets, fill tables files/symbols/references_/calls/imports/endpoints/dir_stats/repo_metrics
        # Minimal placeholder: inventory files relpath, size, mtime, content_hash
        cur = conn.cursor()
        for root, dirs, files in os.walk(path):
            # Skip .git and large vendor dirs quickly
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'vendor', 'dist', 'build', '.venv'}]
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, path)
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                cur.execute(
                    "INSERT INTO files(relpath, size, mtime, content_hash, is_binary, is_test) VALUES (?,?,?,?,?,?)",
                    (rel, int(st.st_size), int(st.st_mtime), _hash_file(full), 0, 1 if '/tests/' in rel or rel.startswith('tests/') else 0)
                )
        conn.commit()
    finally:
        conn.close()

    # Compute integrity hash of db
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
