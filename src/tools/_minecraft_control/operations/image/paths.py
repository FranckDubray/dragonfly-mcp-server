"""
Path utilities for images (docs/images, robust resolution).
"""
import os
from typing import Tuple


def _find_project_root(start: str) -> str:
    cur = os.path.abspath(start)
    for _ in range(8):
        if os.path.isfile(os.path.join(cur, 'pyproject.toml')) or os.path.isdir(os.path.join(cur, '.git')):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


def get_images_base_dir() -> str:
    root = _find_project_root(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(root, 'docs', 'images'))


def normalize_image_path(image_path: str) -> Tuple[str, str, str]:
    """Return (base_dir, rel, original) for image under docs/images.
    Accept absolute paths that contain '/docs/images/'.
    """
    original = (image_path or '').strip()
    base_dir = get_images_base_dir()
    p = original.replace('\\', '/').strip()

    # Absolute path that already points under a docs/images somewhere
    if os.path.isabs(p):
        idx = p.rfind('/docs/images/')
        if idx != -1:
            rel = os.path.normpath(p[idx + len('/docs/images/'):])
            return base_dir, rel, original
        raise ValueError("image_path must be relative to docs/images (no traversal)")

    # Strip common prefixes
    for prefix in ('src/docs/images/', 'docs/images/', './docs/images/', '/docs/images/'):
        if p.startswith(prefix):
            p = p[len(prefix):]
            break
    p = p.lstrip('/')
    rel = os.path.normpath(p)
    if not rel or rel.startswith('..') or os.path.isabs(rel):
        raise ValueError("image_path must be relative to docs/images (no traversal)")
    return base_dir, rel, original


def resolve_candidates(base_dir: str, rel: str, original: str) -> list[str]:
    full_path = os.path.join(base_dir, rel)
    candidates = [full_path]
    cwd_docs = os.path.abspath(os.path.join(os.getcwd(), 'docs', 'images'))
    candidates.append(os.path.join(cwd_docs, rel))
    op = original.replace('\\', '/').lstrip('./')
    if op.startswith('docs/images/'):
        candidates.append(os.path.abspath(os.path.join(os.getcwd(), op)))
    return candidates
