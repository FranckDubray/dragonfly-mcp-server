
from __future__ import annotations
from typing import Any
from pathlib import Path
from .loader import load_module
from .config_merge import merge_worker_config
from ..db import set_state_kv, set_phase
from src.tools._orchestrator.logging.crash_logger import log_crash


def bootstrap_process(root: Path, db_path: str, worker: str) -> tuple[Any, dict, dict]:
    """Load process + subgraphs and return (process, submods, graph_meta).
    Raises exceptions to caller; handles KV side-effects for metadata.
    """
    try:
        proc_mod = load_module(f"pyworker_{worker}_process", root / 'process.py')
    except Exception as e:
        set_phase(db_path, worker, 'failed')
        set_state_kv(db_path, worker, 'last_error', f'Load process failed: {str(e)[:300]}')
        try:
            log_crash(db_path, worker, cycle_id='startup', node='process_import', error=e, worker_ctx={}, cycle_ctx={})
        except Exception:
            pass
        raise
    process = proc_mod.PROCESS

    # Directory-based config merge
    merge_worker_config(root, process, db_path, worker)
    try:
        set_state_kv(db_path, worker, 'py.process_metadata', __import__('json').dumps(process.metadata or {}))
    except Exception:
        pass

    return process
