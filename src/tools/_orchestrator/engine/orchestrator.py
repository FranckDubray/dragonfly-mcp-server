# Thin wrapper preserving public API
from typing import Dict, Any, Callable, Optional
from .orchestrator_core import OrchestratorCore

class OrchestratorEngine(OrchestratorCore):
    def __init__(self, graph: Dict, db_path: str, worker: str, cancel_flag_fn: Callable[[], bool], debug_getter: Optional[Callable[[], Dict[str, Any]]] = None):
        super().__init__(graph, db_path, worker, cancel_flag_fn, debug_getter)
