import os, subprocess, sys
from typing import Tuple

# Project root: 3 levels up from this file: src/tools/_veo_video/utils.py -> src/tools -> src -> project root
CHROOT_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Safe chrooted join under project root

def safe_join(*parts: str) -> str:
    candidate = os.path.abspath(os.path.join(CHROOT_BASE, *parts))
    if not candidate.startswith(CHROOT_BASE + os.sep) and candidate != CHROOT_BASE:
        raise ValueError("Path escape détecté")
    return candidate


def auto_start_video(rel_path: str) -> dict:
    path = safe_join(rel_path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Fichier introuvable: {rel_path}")
    try:
        if sys.platform.startswith('darwin'):
            subprocess.Popen(['open', path])
        elif os.name == 'nt':
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(['xdg-open', path])
        return {"started": True, "path": rel_path}
    except Exception as e:
        return {"started": False, "error": str(e), "path": rel_path}
