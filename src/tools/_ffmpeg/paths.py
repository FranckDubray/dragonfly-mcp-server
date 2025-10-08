from __future__ import annotations
import os


def project_root() -> str:
    # _ffmpeg (this file) -> tools -> src -> project root
    here = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(here, '..', '..', '..'))


def rel_video_path(path: str) -> str:
    # Accept absolute or relative; strip leading slash for consistency
    if not isinstance(path, str):
        return ''
    return path[1:] if path.startswith('/') else path


def abs_from_project(rel_path: str) -> str:
    return os.path.abspath(os.path.join(project_root(), rel_path))


def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def resolves_to_docs_video(p: str) -> bool:
    try:
        # Normalize relative to project root to verify prefix
        rel = os.path.relpath(p, project_root())
        return rel.replace('\\', '/').startswith('docs/video/')
    except Exception:
        return False


def resolve_video_path(input_path: str) -> str | None:
    """Try multiple candidates to find an existing video path while enforcing docs/video/ sandbox."""
    rel = rel_video_path(input_path or '')
    # quick reject if clearly outside sandbox
    if not (rel.startswith('docs/video/') or input_path.startswith('/docs/video/')):
        return None
    candidates = []
    # 1) under project root
    candidates.append(abs_from_project(rel))
    # 2) under current working directory
    candidates.append(os.path.abspath(rel))
    # 3) absolute /docs/video/... (container root)
    if input_path.startswith('/docs/video/'):
        candidates.append(input_path)
    else:
        candidates.append('/' + rel)
    for c in candidates:
        if os.path.exists(c) and resolves_to_docs_video(c):
            return c
    return None
