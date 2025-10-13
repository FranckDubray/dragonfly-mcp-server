import os, re, sqlite3, hashlib, json
from typing import Any, Dict, Optional, Tuple

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

    release_dir = None
    if release_tag:
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
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    try:
        conn.execute("PRAGMA query_only=ON;")
        conn.execute("PRAGMA foreign_keys=ON;")
    except Exception:
        pass
    return conn


def fetch_manifest_for_db(db_path: str) -> Optional[Dict[str, Any]]:
    """Return manifest JSON adjacent to db_path if present."""
    try:
        release_dir = os.path.dirname(os.path.abspath(db_path))
        manifest_path = os.path.join(release_dir, "manifest.json")
        if os.path.isfile(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return None
    return None
