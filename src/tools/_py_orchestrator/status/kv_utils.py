
from typing import Any
from ..db import get_state_kv


def read_kv(db_path: str, worker: str, key: str) -> str:
    try:
        return get_state_kv(db_path, worker, key) or ''
    except Exception:
        return ''
