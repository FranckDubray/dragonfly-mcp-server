import os, re, sqlite3, hashlib, json
from typing import Any, Dict, Optional, Tuple, List

# Keep legacy default based on process CWD (fallback)
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
                    m = re.match(r"\[remote \"([^\"]+)\"\]", s)
                    current_remote = m.group(1) if m else None
                elif current_remote == "origin" and s.lower().startswith("url = "):
                    url = s.split("=", 1)[1].strip()
                    break
        if not url:
            return None
        m = re.search(r"github\.com[/:]([^/]+)/([^/.]+)", url)
        if not m:
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
    """
    Determine target repo slug (used under ./sqlite3/<slug>/...):
    1) Name hint from provided repo_path basename (e.g. path="backend" -> "backend")
    2) Explicit env DEVNAV_REPO_SLUG
    3) Git remote of repo_path (origin)
    4) Fallback: local path basename + short hash
    """
    # 1) Prefer the caller-provided path hint (basename), even if the directory doesn't exist locally
    try:
        base_name = os.path.basename(os.path.abspath(repo_path)) or "repo"
        if base_name not in {"", "."}:
            hint = _sanitize(base_name)
            if hint:
                return hint
    except Exception:
        pass

    # 2) Env override
    env_slug = _slug_from_env()
    if env_slug:
        return env_slug

    # 3) Git remote slug (if repo_path is an actual repo)
    git_slug = _slug_from_git_remote(os.path.abspath(repo_path))
    if git_slug:
        return git_slug

    # 4) Fallback: local path basename + short hash
    base = os.path.basename(os.path.abspath(repo_path)) or "repo"
    h = hashlib.sha1(os.path.abspath(repo_path).encode("utf-8")).hexdigest()[:8]
    return f"{_sanitize(base)}__{h}"


def _git_root_from_path(start_path: str) -> Optional[str]:
    """Walk upwards from start_path to find a directory containing .git."""
    d = os.path.abspath(start_path)
    while True:
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def _sqlite_root_candidates(repo_path: str) -> List[str]:
    """Return candidate sqlite roots in priority order: git_root/sqlite3, CWD/sqlite3, repo_path/sqlite3."""
    candidates: List[str] = []
    # 1) Git root/sqlite3
    git_root = _git_root_from_path(repo_path)
    if git_root:
        candidates.append(os.path.join(git_root, "sqlite3"))
    # 2) CWD/sqlite3 (legacy)
    candidates.append(SQLITE_ROOT)
    # 3) repo_path/sqlite3
    base = os.path.abspath(repo_path if os.path.isabs(repo_path) else os.path.join(os.getcwd(), repo_path))
    candidates.append(os.path.join(base, "sqlite3"))
    # Deduplicate while preserving order
    seen = set()
    out: List[str] = []
    for c in candidates:
        if c not in seen:
            out.append(c)
            seen.add(c)
    return out


def resolve_index_db(repo_path: str, release_tag: Optional[str], commit_hash: Optional[str]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    repo_slug = make_repo_slug(repo_path)

    # Build candidate bases and remember attempts for logging
    bases = _sqlite_root_candidates(repo_path)
    attempts: List[str] = [os.path.join(b, repo_slug) for b in bases]

    repo_dir = None
    for base in attempts:
        if os.path.isdir(base):
            repo_dir = base
            break

    if not repo_dir:
        return None, {
            "code": "release_index_missing",
            "message": f"No index for repo_slug={repo_slug}; searched=[{', '.join(attempts)}]",
            "scope": "tool",
            "recoverable": True
        }

    release_dir = None
    searched_variants: List[str] = []

    if release_tag:
        for name in sorted(os.listdir(repo_dir)):
            path = os.path.join(repo_dir, name)
            if name.startswith(f"{release_tag}__") and os.path.isdir(path):
                searched_variants.append(path)
                if commit_hash:
                    short = commit_hash[:8]
                    if f"__{short}" in name:
                        release_dir = path
                        break
                else:
                    release_dir = path
                    break
    elif commit_hash:
        short = commit_hash[:8]
        for name in sorted(os.listdir(repo_dir)):
            path = os.path.join(repo_dir, name)
            if name.endswith(f"__{short}") and os.path.isdir(path):
                searched_variants.append(path)
                release_dir = path
                break
    else:
        cand = os.path.join(repo_dir, "latest")
        searched_variants.append(cand)
        if os.path.isdir(cand):
            release_dir = cand

    if not release_dir:
        return None, {
            "code": "release_index_missing",
            "message": (
                f"No matching release for repo_slug={repo_slug}; base={repo_dir}; "
                f"tag={release_tag or '-'}, commit={commit_hash or '-'}; "
                f"tried=[{', '.join(searched_variants) or '-'}]"
            ),
            "scope": "tool",
            "recoverable": True
        }

    db_path = os.path.join(release_dir, "index.db")
    if not os.path.isfile(db_path):
        return None, {
            "code": "release_index_missing",
            "message": f"index.db not found: {db_path}",
            "scope": "tool",
            "recoverable": True
        }
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
