




from typing import Dict, Any, Tuple
from pathlib import Path
import json

from ..controller import validate_and_extract_graph, ValidationError
from ..db import set_phase, set_state_kv
from src.tools._orchestrator.logging.crash_logger import log_crash


def preflight_load_graph(root: Path, db_path: str, worker: str) -> Tuple[Dict[str, Any] | None, str]:
    """Validate and extract the graph. Returns (graph, error_msg).
    On failure, handles phase, last_error, and crash log, then returns (None, msg).
    """
    try:
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
