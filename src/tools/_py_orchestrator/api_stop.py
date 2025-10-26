
from pathlib import Path
from .validators import validate_params
from .._orchestrator.api_spawn import db_path_for_worker
from .._orchestrator.api_stop import stop as stop_json  # reuse signals/logic


def stop(params: dict) -> dict:
    # validate only worker_name/mode for py orchestrator
    p = validate_params(params)
    # delegate to JSON orchestrator stop (same DB path and signals)
    return stop_json({**p, 'operation': 'stop'})
