# Orchestrator Core (post-split aggregator) — see core_nodes_*.py for logic
from typing import Dict, Any, Callable, Optional
import copy
import os

from .core_nodes_common import begin_node, exec_start_node, exec_end_or_exit_node, apply_resets_before
from .core_nodes_handler import execute_handler_node
from .core_nodes_decision import execute_decision_node
from ..logging.crash_logger import log_crash
from .orchestrator_edges import follow_edge, get_scope_trigger, get_available_routes
from .orchestrator_scopes import apply_scope_trigger
from ..logging import end_step
from ..handlers import HandlerError
from ..policies import RetryExhaustedError
from .debug_utils import DebugPause, _preview, is_truncated_preview
from ..context import resolve_inputs, resolve_value


class OrchestratorCore:
    # Default ceiling (overridable via ORCHESTRATOR_MAX_NODES_PER_CYCLE)
    MAX_NODES_PER_CYCLE = 1000

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
        # Instance-level max nodes per cycle (env override)
        try:
            env_val = os.environ.get('ORCHESTRATOR_MAX_NODES_PER_CYCLE')
            self.max_nodes_per_cycle = int(env_val) if env_val else int(self.MAX_NODES_PER_CYCLE)
        except Exception:
            self.max_nodes_per_cycle = int(self.MAX_NODES_PER_CYCLE)

    # Exposed for debug inspector
    def get_last_step(self) -> Optional[Dict[str, Any]]:
        return self._last_step

    def get_last_ctx_diff(self) -> Optional[Dict[str, Any]]:
        return self._last_ctx_diff

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
            if traversed > self.max_nodes_per_cycle:
                err = RuntimeError(
                    f"Cycle {cycle_id}: {traversed} nodes traversed (max {self.max_nodes_per_cycle})"
                )
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

                # If EXIT encountered, stop external run
                if node.get('type') == 'exit':
                    return True

                # END reboucle to START automatically
                if node.get('type') == 'end':
                    start = self.find_start()
                    if not start:
                        raise ValueError("END encountered but no START node found to reloop")
                    current_node_name = start['name']
                    continue

                # Compute next node from routing
                next_node = follow_edge(current_node_name, route, self.edges)
                scope_trig = get_scope_trigger(current_node_name, route, self.edges)
                if scope_trig:
                    apply_scope_trigger(scope_trig, cycle_ctx, self.scopes)

                # DEBUG GATING: pause after node if requested
                try:
                    if self.debug_getter is not None:
                        dbg = self.debug_getter() or {}
                        from .debug_utils import should_pause_after, DebugPause as _DbgPause
                        if should_pause_after(dbg, node, route):
                            # Hand off next_node to runner loop
                            raise _DbgPause(next_node)
                except Exception:
                    # Never let debug gating crash normal execution
                    pass

                current_node_name = next_node
            except DebugPause:
                # Propagate debug pause without marking failure
                raise
            except Exception as e:
                # Build normalized error details for step failure
                name = node.get('name')
                ntype = node.get('type')
                details: Dict[str, Any] = {
                    "node": name,
                    "type": ntype,
                    "handler_kind": node.get('handler')
                }
                # Attach IO context preview when possible
                try:
                    if ntype in {'io', 'transform'}:
                        inputs_spec = node.get('inputs', {}) or {}
                        inputs_resolved = resolve_inputs(inputs_spec, worker_ctx, cycle_ctx)
                        dp = {"inputs": _preview(inputs_resolved)}
                        details['debug_preview'] = dp
                        if is_truncated_preview(dp):
                            details['truncated'] = True
                    elif ntype == 'decision':
                        spec = node.get('decision', {}) or {}
                        inp_res = resolve_value(spec.get('input'), worker_ctx, cycle_ctx)
                        spec_res = resolve_value(spec, worker_ctx, cycle_ctx)
                        dp = {"inputs": _preview({"decision": {"kind": spec.get('kind'), "spec": spec_res}, "input_resolved": inp_res, "available_routes": get_available_routes(name, self.edges)})}
                        details['debug_preview'] = dp
                        if is_truncated_preview(dp):
                            details['truncated'] = True
                except Exception:
                    pass

                # Error normalization
                if isinstance(e, HandlerError):
                    details["error"] = {
                        "message": e.message,
                        "code": e.code,
                        "category": e.category,
                        "retryable": e.retryable,
                        "details": e.details or {}
                    }
                elif isinstance(e, RetryExhaustedError):
                    he = e.last_error
                    details["attempts"] = getattr(e, "attempts", None)
                    details["error"] = {
                        "message": getattr(he, "message", str(e))[:400],
                        "code": getattr(he, "code", "RETRY_EXHAUSTED"),
                        "category": getattr(he, "category", "io"),
                        "retryable": getattr(he, "retryable", False),
                        "details": getattr(he, "details", {}) or {}
                    }
                else:
                    details["error"] = {
                        "message": str(e)[:400],
                        "type": type(e).__name__
                    }
                # Write failed step and crash log (best effort)
                try:
                    end_step(self.db_path, self.worker, cycle_id, name, 'failed', started_at, details)
                except Exception:
                    pass
                try:
                    log_crash(self.db_path, self.worker, cycle_id, name, e, worker_ctx, cycle_ctx)
                except Exception:
                    pass
                # Re-raise to keep current runner behavior
                raise
            finally:
                try:
                    from ..db import set_state_kv
                    set_state_kv(self.db_path, self.worker, 'debug.executing_node', '')
                except Exception:
                    pass
        return False
