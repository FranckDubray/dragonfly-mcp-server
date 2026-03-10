from __future__ import annotations

from pathlib import Path


def build_run_name(corpus: str, mode: str, archive_name: str) -> str:
    archive_slug = archive_name.replace('.tar.gz', '').replace('/', '_')
    return f"{corpus}_{mode}_{archive_slug}"


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
