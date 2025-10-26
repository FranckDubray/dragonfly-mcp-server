
import hashlib
from pathlib import Path

EXCLUDE_EXT = {'.pyc', '.pyo'}
EXCLUDE_DIRS = {'__pycache__'}


def compute_dir_uid(root: Path) -> str:
    """Compute a stable SHA256 hash for all files under root (names+contents)."""
    h = hashlib.sha256()
    root = Path(root)
    for p in sorted(root.rglob('*')):
        if p.is_dir() and p.name in EXCLUDE_DIRS:
            continue
        if p.is_file() and p.suffix.lower() in EXCLUDE_EXT:
            continue
        rel = p.relative_to(root).as_posix().encode('utf-8')
        h.update(rel)
        if p.is_file():
            try:
                h.update(p.read_bytes())
            except Exception:
                pass
    return h.hexdigest()[:12]
