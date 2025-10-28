"""
Validation de chemins pour médias locaux.
- Lecture seule, sous base_dir=./docs.
- Autorise sous-dossiers: images, video.
- Refuse: chemins absolus, .., lecteurs externes.
Aucune I/O à l'import.
"""
from __future__ import annotations

import os
from typing import Tuple

BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), 'docs'))
ALLOWED_SUBDIRS = {"images", "video"}


def normalize_local_path(user_path: str) -> Tuple[bool, str | None, str | None]:
    """Retourne (ok, abs_path, error_code)."""
    if not isinstance(user_path, str) or not user_path:
        return False, None, "invalid_path"
    # Interdit absolu
    if os.path.isabs(user_path):
        return False, None, "absolute_forbidden"
    # Normaliser relatif à BASE_DIR
    candidate = os.path.abspath(os.path.join(BASE_DIR, user_path.replace('\r', '').replace('\n', '')))
    # Doit être sous BASE_DIR
    if not candidate.startswith(BASE_DIR + os.sep):
        return False, None, "outside_base"
    # Doit contenir un sous-dossier autorisé
    rel = os.path.relpath(candidate, BASE_DIR)
    parts = rel.split(os.sep)
    if not parts or parts[0] not in ALLOWED_SUBDIRS:
        return False, None, "subdir_forbidden"
    return True, candidate, None
