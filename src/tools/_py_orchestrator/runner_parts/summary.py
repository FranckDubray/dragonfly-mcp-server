from typing import Dict, Any
from ..db import set_state_kv


def persist_summary_if_any(db_path: str, worker: str, cycle: Dict[str, Any]):
    try:
        summary = cycle.get('summary')
        if isinstance(summary, str):
            if len(summary) > 4000:
                summary = summary[:4000] + "\n... (truncated)"
            set_state_kv(db_path, worker, 'py.last_summary', summary)
    except Exception:
        pass
