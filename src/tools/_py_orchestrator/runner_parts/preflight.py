











from typing import Dict, Any, Tuple
from pathlib import Path
import json
import os

from ..controller import validate_and_extract_graph, ValidationError
from ..db import set_phase, set_state_kv
from ..logging.crash_logger import log_crash
from .preflight_checks import preflight_extra_checks

# NEW unified core
from ..validation_core import validate_full


def _env_truthy(name: str) -> bool:
    try:
        v = os.getenv(name)
        if v is None:
            return False
        s = str(v).strip().lower()
        return s in {"1","true","yes","on"}
    except Exception:
        return False


def preflight_load_graph(root: Path, db_path: str, worker: str) -> Tuple[Dict[str, Any] | None, str]:
    """
    Validate and extract the graph using the unified core. Returns (graph, error_msg).
    On failure, handles phase, last_error, and crash log, then returns (None, msg).
    Also runs extra controller-level checks (handlers/tool_specs presence, reachability).
    """
    try:
        # Use unified core with persist=True so KV effects and phase are set on errors
        res = validate_full(worker, include_preflight=True, persist=True)
        if not isinstance(res, dict):
            set_phase(db_path, worker, 'failed')
            set_state_kv(db_path, worker, 'last_error', 'Preflight internal error')
            return None, 'Preflight internal error'
        if not res.get('accepted'):
            msg = 'Preflight checks failed'
            set_phase(db_path, worker, 'failed')
            set_state_kv(db_path, worker, 'last_error', msg)
            return None, msg
        # When accepted, extract graph again from filesystem to return it (or fetch from res if needed)
        graph = validate_and_extract_graph(root)
        return graph, ""
    except ValidationError as e:
        set_phase(db_path, worker, 'failed')
        msg = f'Validation error: {str(e)[:300]}'
        set_state_kv(db_path, worker, 'last_error', msg)
        try:
            log_crash(db_path, worker, cycle_id='startup', node='controller_validate', error=e, worker_ctx={}, cycle_ctx={})
        except Exception:
            pass
        return None, msg
    except Exception as e:
        set_phase(db_path, worker, 'failed')
        msg = f'Unexpected preflight error: {str(e)[:300]}'
        set_state_kv(db_path, worker, 'last_error', msg)
        try:
            log_crash(db_path, worker, cycle_id='startup', node='controller_validate', error=e, worker_ctx={}, cycle_ctx={})
        except Exception:
            pass
        return None, msg


def set_graph_metadata(db_path: str, worker: str, graph: Dict[str, Any]) -> None:
    try:
        set_state_kv(db_path, worker, 'py.graph_mermaid', graph.get('mermaid',''))
        set_state_kv(db_path, worker, 'py.process_metadata', json.dumps(graph.get('metadata') or {}))
    except Exception:
        pass
