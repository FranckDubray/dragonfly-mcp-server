




from typing import Dict, Any, Tuple
from pathlib import Path
import json
import os

from ..controller import validate_and_extract_graph, ValidationError
from ..db import set_phase, set_state_kv
from src.tools._orchestrator.logging.crash_logger import log_crash
from .preflight_checks import preflight_extra_checks


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
    """Validate and extract the graph. Returns (graph, error_msg).
    On failure, handles phase, last_error, and crash log, then returns (None, msg).
    Also runs extra controller-level checks (handlers/tool_specs presence, reachability).
    """
    try:
        graph = validate_and_extract_graph(root)
        # Decide strict tools policy: ENV first, then metadata.strict_tools
        strict_tools = False
        try:
            strict_tools = _env_truthy('PY_ORCH_STRICT_TOOLS') or bool((graph.get('metadata') or {}).get('strict_tools'))
        except Exception:
            strict_tools = _env_truthy('PY_ORCH_STRICT_TOOLS')
        # Extra checks (non-destructive)
        ok = preflight_extra_checks(graph, db_path, worker, strict_tools=strict_tools)
        if not ok:
            return None, 'Preflight checks failed'
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

 
 
 
 
 
