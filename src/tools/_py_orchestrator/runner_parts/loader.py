from pathlib import Path
import importlib.util
import sys

from ..validators import PY_WORKERS_DIR


def load_worker_root(worker_name: str) -> Path:
    return PY_WORKERS_DIR / worker_name


def load_module(mod_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod
