import os, re, sqlite3, hashlib, json
from typing import Any, Dict, Optional, Tuple

SQLITE_ROOT = os.path.abspath(os.path.join(os.getcwd(), "sqlite3"))


def _sanitize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9_\-]+", "-", s)
    return s.strip("-")


def _slug_from_env() -> Optional[str]:
    v = os.getenv("DEVNAV_REPO_SLUG")
    if v:
        return _sanitize(v)
    return None


def _slug_from_git_remote(repo_path: str) -> Optional[str]:
    # Parse .git/config to extract remote "origin" url and derive a stable slug
    try:
        cfg = os.path.join(repo_path, ".git", "config")
        if not os.path.isfile(cfg):
            return None
        url = None
        current_remote = None
        with open(cfg, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                s = line.strip()
                if s.startswith("[remote "):
                    # [remote "origin"]
                    m = re.match(r"\[remote \"([^\"]+)\"\]", s)
                    current_remote = m.group(1) if m else None
                elif current_remote == "origin" and s.lower().startswith("url = "):
                    url = s.split("=", 1)[1].strip()
                    break
        if not url:
            return None
        # Extract owner/repo from URL
        # Supports https://github.com/Owner/Repo.git or git@github.com:Owner/Repo.git
        m = re.search(r"github\.com[/:]([^/]+)/([^/.]+)", url)
        if not m:
            # Fallback: take last two path parts
            parts = re.split(r"[/:]", url)
            parts = [p for p in parts if p]
            if len(parts) >= 2:
                owner, repo = parts[-2], parts[-1].split(".")[0]
            else:
                return None
        else:
            owner, repo = m.group(1), m.group(2)
        slug = f"{owner}-{repo}"
        return _sanitize(slug)
    except Exception:
        return None


def make_repo_slug(repo_path: str) -> str:
    # Priority: explicit env → git remote → local path hash
    env_slug = _slug_from_env()
    if env_slug:
        return env_slug
    git_slug = _slug_from_git_remote(os.path.abspath(repo_path))
    if git_slug:
        return git_slug
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
    try:
        release_dir = os.path.dirname(os.path.abspath(db_path))
        manifest_path = os.path.join(release_dir, "manifest.json")
        if os.path.isfile(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return None
    return None
