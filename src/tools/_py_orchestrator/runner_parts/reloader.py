
from typing import Dict, Any, Tuple
from pathlib import Path
from ..hash_utils import compute_dir_uid
from ..controller import validate_and_extract_graph
from ..db import set_state_kv, set_phase
from ..logging.crash_logger import log_crash
from .loader import load_module
from .preflight import set_graph_metadata


def maybe_hot_reload(root: Path, db_path: str, worker: str, uid: str) -> Tuple[str, Dict[str, Any], Any, Dict[str, Any], list, Dict[str, Any], str, str] | Tuple[str, None, None, None, None, None, None, None]:
    """
    If files changed, reload process + subgraphs and return updated structures.
    Returns (new_uid, graph, process, submods, order, subgraph_infos, current_sub, current_step)
    or (uid, None, None, None, None, None, None, None) if no change.
    """
    new_uid = compute_dir_uid(root)
    if new_uid == uid:
        return uid, None, None, None, None, None, None, None
    try:
        graph = validate_and_extract_graph(root)
        set_graph_metadata(db_path, worker, graph)
        proc_mod = load_module(f"pyworker_{worker}_process", root / 'process.py')
        process = proc_mod.PROCESS
        submods: Dict[str, Any] = {}
        for ref in process.parts:
            mod = load_module(f"pyworker_{worker}_{ref.name}", root / (ref.module.replace('.', '/') + '.py'))
            submods[ref.name] = mod
        order = graph.get('order') or []
        subgraph_infos: Dict[str, Any] = graph.get('subgraphs', {})
        current_sub = process.entry
        current_step = submods[current_sub].SUBGRAPH.entry
        return new_uid, graph, process, submods, order, subgraph_infos, current_sub, current_step
    except Exception as e:
        set_phase(db_path, worker, 'failed')
        set_state_kv(db_path, worker, 'last_error', f'Hot reload failed: {str(e)[:300]}')
        try:
            log_crash(db_path, worker, cycle_id='hot_reload', node='hot_reload', error=e, worker_ctx={}, cycle_ctx={})
        except Exception:
            pass
        return uid, None, None, None, None, None, None, None
