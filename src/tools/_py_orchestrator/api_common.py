
from pathlib import Path
from .validators import PY_WORKERS_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SQLITE_DIR = PROJECT_ROOT / 'sqlite3'
LOG_DIR = PROJECT_ROOT / 'logs'

__all__ = ['PROJECT_ROOT','SQLITE_DIR','LOG_DIR','PY_WORKERS_DIR']
