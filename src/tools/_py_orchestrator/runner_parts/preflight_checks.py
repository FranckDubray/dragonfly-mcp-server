
from __future__ import annotations
from typing import Dict, Any

from ..db import set_phase, set_state_kv
from ..controller_parts.graph_checks import run_all_checks


def preflight_extra_checks(graph: Dict[str, Any], db_path: str, worker: str, *, strict_tools: bool = False) -> bool:
    """Run extra preflight checks. Persist warnings into KV; set failed phase on errors.
    Returns True if ok, False if errors.

    Important: ensure stale warnings/errors do not persist across successful runs.
    - When no warnings: clear 'py.graph_warnings'.
    - When no errors: clear 'py.graph_errors'.
    """
    errors, warnings = run_all_checks(graph, strict_tools=strict_tools)

    # Persist or clear warnings
    try:
        import json
        if warnings:
            set_state_kv(db_path, worker, 'py.graph_warnings', json.dumps(warnings, ensure_ascii=False))
        else:
            # Clear stale warnings from previous runs
            set_state_kv(db_path, worker, 'py.graph_warnings', '')
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

    # Clear stale errors if present from a previous failed attempt
    try:
        set_state_kv(db_path, worker, 'py.graph_errors', '')
    except Exception:
        pass

    return True
