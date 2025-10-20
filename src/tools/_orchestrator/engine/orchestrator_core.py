# Orchestrator Core (post-split aggregator) — see core_nodes_*.py for logic
from typing import Dict, Any, Callable, Optional
import copy

from .core_nodes_common import begin_node, exec_start_node, exec_end_or_exit_node, apply_resets_before
from .core_nodes_handler import execute_handler_node
from .core_nodes_decision import execute_decision_node
from ..logging.crash_logger import log_crash
from .orchestrator_edges import follow_edge, get_scope_trigger
from .orchestrator_scopes import apply_scope_trigger

class OrchestratorCore:
    MAX_NODES_PER_CYCLE = 100

    def __init__(self, graph: Dict, db_path: str, worker: str,
                 cancel_flag_fn: Callable[[], bool],
                 debug_getter: Optional[Callable[[], Dict[str, Any]]] = None):
        self.graph = graph
        self.db_path = db_path
        self.worker = worker
        self.cancel_flag_fn = cancel_flag_fn
        from ..handlers import get_registry
        self.registry = get_registry()
        self.debug_getter = debug_getter
        self.nodes = {n['name']: n for n in graph.get('nodes', [])}
        self.edges = graph.get('edges', [])
        self.scopes = graph.get('scopes', [])
        self._last_step: Optional[Dict[str, Any]] = None
        self._last_ctx_diff: Optional[Dict[str, Any]] = None

    def find_start(self) -> Optional[Dict]:
        for node in self.nodes.values():
            if node.get('type') == 'start':
                return node
        return None

    def run_cycle(self, cycle_id: str, worker_ctx: Dict, cycle_ctx: Dict, start_from_node: Optional[str] = None) -> bool:
        current_node_name = start_from_node or (self.find_start()['name'] if self.find_start() else None)
        if not current_node_name:
            raise ValueError("No START node found in graph")
        traversed = 0
        while current_node_name and not self.cancel_flag_fn():
            traversed += 1
            if traversed > self.MAX_NODES_PER_CYCLE:
                err = RuntimeError(f"Cycle {cycle_id}: {traversed} nodes traversed (max {self.MAX_NODES_PER_CYCLE})")
                log_crash(self.db_path, self.worker, cycle_id, current_node_name, err, worker_ctx, cycle_ctx)
                raise err
            node = self.nodes.get(current_node_name)
            if not node:
                raise ValueError(f"Node not found: {current_node_name}")

            # Expose current node in state
            try:
                from ..db import set_state_kv
                set_state_kv(self.db_path, self.worker, 'current_node', current_node_name)
                set_state_kv(self.db_path, self.worker, 'debug.executing_node', current_node_name)
            except Exception:
                pass

            started_at = begin_node(self, cycle_id, node)

            try:
                ntype = node.get('type', 'io')
                if ntype == 'start':
                    route = exec_start_node(self, cycle_id, node, cycle_ctx)
                elif ntype in {'end', 'exit'}:
                    route = exec_end_or_exit_node(self, cycle_id, node)
                else:
                    apply_resets_before(self, node, cycle_ctx)
                    if ntype in {'io', 'transform'}:
                        route = execute_handler_node(self, cycle_id, node, worker_ctx, cycle_ctx, started_at)
                    elif ntype == 'decision':
                        route = execute_decision_node(self, cycle_id, node, worker_ctx, cycle_ctx, started_at)
                    else:
                        raise ValueError(f"Unknown node type: {ntype}")

                # Routing
                if node.get('type') == 'exit':
                    return True
                if node.get('type') == 'end':
                    start = self.find_start()
                    if not start:
                        raise ValueError("END encountered but no START node found to reloop")
                    current_node_name = start['name']
                    continue

                next_node = follow_edge(current_node_name, route, self.edges)
                scope_trig = get_scope_trigger(current_node_name, route, self.edges)
                if scope_trig:
                    apply_scope_trigger(scope_trig, cycle_ctx, self.scopes)

                current_node_name = next_node

            finally:
                try:
                    from ..db import set_state_kv
                    set_state_kv(self.db_path, self.worker, 'debug.executing_node', '')
                except Exception:
                    pass
        return False
