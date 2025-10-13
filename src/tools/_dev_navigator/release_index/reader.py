import os, re, sqlite3, hashlib
from typing import Any, Dict, Optional, Tuple, List

SQLITE_ROOT = os.path.abspath(os.path.join(os.getcwd(), "sqlite3"))


def _sanitize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9_\-]+", "-", s)
    return s.strip("-")


def make_repo_slug(repo_path: str) -> str:
    base = os.path.basename(os.path.abspath(repo_path)) or "repo"
    h = hashlib.sha1(os.path.abspath(repo_path).encode("utf-8")).hexdigest()[:8]
    return f"{_sanitize(base)}__{h}"


def resolve_index_db(repo_path: str, release_tag: Optional[str], commit_hash: Optional[str]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    repo_slug = make_repo_slug(repo_path)
    repo_dir = os.path.join(SQLITE_ROOT, repo_slug)
    if not os.path.isdir(repo_dir):
        return None, {"code": "release_index_missing", "message": f"No index for repo_slug={repo_slug}", "scope": "tool", "recoverable": True}

    # Select release directory
    release_dir = None
    if release_tag:
        # Find dirs like <tag>__<shortsha>
        for name in sorted(os.listdir(repo_dir)):
            if name.startswith(f"{release_tag}__") and os.path.isdir(os.path.join(repo_dir, name)):
                if commit_hash:
                    short = commit_hash[:8]
                    if f"__{short}" in name:
                        release_dir = os.path.join(repo_dir, name)
                        break
                else:
                    release_dir = os.path.join(repo_dir, name)
                    break
    elif commit_hash:
        short = commit_hash[:8]
        for name in sorted(os.listdir(repo_dir)):
            if name.endswith(f"__{short}") and os.path.isdir(os.path.join(repo_dir, name)):
                release_dir = os.path.join(repo_dir, name)
                break
    else:
        # Fallback to latest symlink/folder
        cand = os.path.join(repo_dir, "latest")
        if os.path.isdir(cand):
            release_dir = cand

    if not release_dir:
        return None, {"code": "release_index_missing", "message": "No matching release (tag/commit/latest)", "scope": "tool", "recoverable": True}

    db_path = os.path.join(release_dir, "index.db")
    if not os.path.isfile(db_path):
        return None, {"code": "release_index_missing", "message": "index.db not found in release dir", "scope": "tool", "recoverable": True}
    return db_path, None


def _open_ro(db_path: str) -> sqlite3.Connection:
    # Open in read-only mode using URI
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    try:
        conn.execute("PRAGMA query_only=ON;")
        conn.execute("PRAGMA foreign_keys=ON;")
    except Exception:
        pass
    return conn


# Query helpers (defensive)

def query_symbol_info(conn: sqlite3.Connection, fqname: Optional[str], symbol_key: Optional[str], path: Optional[str], line: Optional[int]) -> Optional[Dict[str, Any]]:
    cur = conn.cursor()
    try:
        if fqname or symbol_key:
            if fqname:
                cur.execute("SELECT id,file_id,lang,name,fqname,kind,signature,start_line,start_col,end_line,end_col FROM symbols WHERE fqname=? LIMIT 1", (fqname,))
            else:
                cur.execute("SELECT id,file_id,lang,name,fqname,kind,signature,start_line,start_col,end_line,end_col FROM symbols WHERE symbol_key=? LIMIT 1", (symbol_key,))
        elif path and line is not None:
            cur.execute(
                """
                SELECT s.id,s.file_id,s.lang,s.name,s.fqname,s.kind,s.signature,s.start_line,s.start_col,s.end_line,s.end_col
                FROM symbols s
                JOIN files f ON s.file_id=f.id
                WHERE f.relpath=? AND (? >= s.start_line AND ? <= COALESCE(s.end_line, s.start_line))
                ORDER BY (COALESCE(s.end_line, s.start_line) - s.start_line) ASC
                LIMIT 1
                """,
                (path, line, line),
            )
        else:
            return None
        row = cur.fetchone()
        if not row:
            return None
        # Fetch file path deterministically
        fpath = None
        try:
            cur2 = conn.cursor()
            cur2.execute("SELECT relpath FROM files WHERE id=?", (row[1],))
            r2 = cur2.fetchone()
            fpath = r2[0] if r2 else None
        finally:
            try:
                cur2.close()
            except Exception:
                pass
        return {
            "id": row[0],
            "file_id": row[1],
            "lang": row[2],
            "name": row[3],
            "fqname": row[4],
            "kind": row[5],
            "signature": row[6],
            "anchor": {"path": fpath, "start_line": row[7], "start_col": row[8], "end_line": row[9], "end_col": row[10]},
        }
    finally:
        cur.close()

# ... rest unchanged ...
