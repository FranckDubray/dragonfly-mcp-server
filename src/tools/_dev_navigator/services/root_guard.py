import os


def project_root() -> str:
    # Treat current working directory as project root (server runs from repo root)
    return os.path.abspath(os.getcwd())


def ensure_under_project_root(path: str) -> str:
    """Return absolute path if it resides under project root, else raise ValueError."""
    base = project_root()
    abs_path = os.path.abspath(os.path.join(base, path)) if not os.path.isabs(path) else os.path.abspath(path)
    if not abs_path.startswith(base + os.sep) and abs_path != base:
        raise ValueError("path escapes project root")
    return abs_path
