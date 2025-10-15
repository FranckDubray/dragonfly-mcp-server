import os


def project_root() -> str:
    # Treat current working directory as project root (server runs from repo root)
    return os.path.abspath(os.getcwd())


def clones_root() -> str:
    """Return the parent directory of the project root (allowed read-only area for sibling repos)."""
    return os.path.abspath(os.path.join(project_root(), os.pardir))


def ensure_under_allowed_roots(path: str) -> str:
    """
    Resolve an absolute path that must reside either under the project root (./) or under
    the clones root (../). This allows targeting sibling repositories with path="<repo>"
    while preserving a chroot-like guard to two known roots.
    - Absolute inputs are accepted only if they stay under one of the allowed roots.
    - Relative inputs are first resolved under project_root(); if that path does not exist,
      fallback to clones_root()/path to support $cwd/../$path layout.
    """
    base_proj = project_root()
    base_clone = clones_root()

    def _is_under(base: str, abs_path: str) -> bool:
        return abs_path == base or abs_path.startswith(base + os.sep)

    if os.path.isabs(path):
        abs_path = os.path.abspath(path)
        if _is_under(base_proj, abs_path) or _is_under(base_clone, abs_path):
            return abs_path
        raise ValueError("path escapes allowed roots")

    # Relative path: prefer project root if it exists, else fallback to clones root
    cand_proj = os.path.abspath(os.path.join(base_proj, path))
    if _is_under(base_proj, cand_proj) and os.path.exists(cand_proj):
        return cand_proj

    cand_clone = os.path.abspath(os.path.join(base_clone, path))
    if _is_under(base_clone, cand_clone):
        return cand_clone

    # If neither exists, keep under project root to avoid surprising escapes
    return cand_proj
