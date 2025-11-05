
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional

from .api_common import PROJECT_ROOT


def relpath_from_root(abs_path: str) -> str:
    try:
        p = Path(abs_path).resolve()
        root = PROJECT_ROOT.resolve()
        return p.relative_to(root).as_posix()
    except Exception:
        return abs_path


def resolve_worker_file_safe(worker_name: str, worker_file: Optional[str]) -> Optional[str]:
    """Ergonomie: si worker_file est relatif ou absent, tenter workers/<name>/process.py.
    Retourne un chemin relatif 'workers/<name>/process.py' si trouvable, sinon None.
    """
    try:
        if worker_file and (worker_file.startswith('workers/') or worker_file.startswith('./workers/')):
            return worker_file
        candidate = Path(PROJECT_ROOT) / 'workers' / worker_name / 'process.py'
        if candidate.is_file():
            return candidate.relative_to(PROJECT_ROOT).as_posix()
    except Exception:
        pass
    return None


def slugify(s: str) -> str:
    import re
    return re.sub(r"[^a-z0-9_]+", "_", s.lower()).strip("_")


def derive_from_template(params: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Si l'appel fournit new_worker:{first_name, template}, dériver worker_name et worker_file automatiquement.
    - worker_name = f"{template}_{first_name}" (slugifié)
    - worker_file = workers/<template>/process.py (doit exister)
    """
    try:
        nw = (params or {}).get('new_worker') or {}
        first = str(nw.get('first_name') or '').strip()
        template = str(nw.get('template') or '').strip()
        if not first or not template:
            return None
        wn = f"{slugify(template)}_{slugify(first)}"
        wf_candidate = (Path(PROJECT_ROOT) / 'workers' / template / 'process.py')
        if not wf_candidate.is_file():
            wf_candidate = (Path(PROJECT_ROOT) / 'workers' / slugify(template) / 'process.py')
        if not wf_candidate.is_file():
            raise FileNotFoundError(f"Template not found: workers/{template}/process.py")
        return {
            'worker_name': wn,
            'worker_file': wf_candidate.relative_to(PROJECT_ROOT).as_posix(),
        }
    except Exception:
        return None
