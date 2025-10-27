
from __future__ import annotations
from typing import Tuple, List, Any
from pathlib import Path
import importlib.util
import sys

from .errors import ValidationError


def _load_module_from_path(mod_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ValidationError("Cannot load module: %s" % file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def discover_funcs(sg_mod) -> Tuple[List[str], List[str]]:
    steps, conds = [], []
    for attr in dir(sg_mod):
        fn = getattr(sg_mod, attr)
        if callable(fn) and getattr(fn, '_py_orch_step', False):
            steps.append(getattr(fn, '_py_orch_step_name'))
        if callable(fn) and getattr(fn, '_py_orch_cond', False):
            conds.append(getattr(fn, '_py_orch_step_name'))
    return steps, conds


def _is_process_like(obj: Any) -> bool:
    try:
        return hasattr(obj, 'entry') and hasattr(obj, 'parts') and hasattr(obj, 'metadata')
    except Exception:
        return False


def _is_subgraphref_like(obj: Any) -> bool:
    try:
        return hasattr(obj, 'name') and hasattr(obj, 'module')
    except Exception:
        return False
