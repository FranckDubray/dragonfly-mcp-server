
from __future__ import annotations
from typing import Dict, Any

from ..db import set_phase, set_state_kv
from ..controller_parts.graph_checks import run_all_checks


def preflight_extra_checks(graph: Dict[str, Any], db_path: str, worker: str, *, strict_tools: bool = False) -> bool:
    """Run extra preflight checks. Persist warnings into KV; set failed phase on errors.
    Returns True if ok, False if errors.
    """
    errors, warnings = run_all_checks(graph, strict_tools=strict_tools)
    if warnings:
        try:
            import json
            set_state_kv(db_path, worker, 'py.graph_warnings', json.dumps(warnings, ensure_ascii=False))
        except Exception:
            pass
    if errors:
        try:
            import json
            set_state_kv(db_path, worker, 'last_error', "; ".join(errors)[:400])
            set_state_kv(db_path, worker, 'py.graph_errors', json.dumps(errors, ensure_ascii=False))
            set_phase(db_path, worker, 'failed')
        except Exception:
            pass
        return False
    return True
