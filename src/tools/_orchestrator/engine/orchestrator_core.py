# Orchestrator core - Main execution loop (refactored <7KB)

from typing import Dict, Any, Callable, Optional
from datetime import datetime, timezone
from ..context import resolve_inputs, assign_outputs
from ..handlers import get_registry, HandlerError
from ..logging import begin_step, end_step, log_retry_attempt
from ..logging.crash_logger import log_crash
from ..policies import execute_with_retry, RetryExhaustedError
from .decisions import evaluate_decision, DecisionError
from .debug_utils import compute_ctx_diff, mk_step_summary, should_pause_after
from .orchestrator_scopes import apply_scopes_at_start, apply_scope_resets, apply_scope_trigger
from .orchestrator_edges import get_available_routes, follow_edge, get_scope_trigger
import copy

class OrchestratorCore:
    MAX_NODES_PER_CYCLE = 100

    def __init__(self, graph: Dict, db_path: str, worker: str,
                 cancel_flag_fn: Callable[[], bool],
                 debug_getter: Optional[Callable[[], Dict[str, Any]]] = None):
        self.graph = graph
        self.db_path = db_path
        self.worker = worker
        self.cancel_flag_fn = cancel_flag_fn
        self.registry = get_registry()
        self.debug_getter = debug_getter
        self.nodes = {n['name']: n for n in graph.get('nodes', [])}
        self.edges = graph.get('edges', [])
        self.scopes = graph.get('scopes', [])
        self._last_step: Optional[Dict[str, Any]] = None
        self._last_ctx_diff: Optional[Dict[str, Any]] = None

    @staticmethod
    def _utcnow_str() -> str:
        return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')

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
            try:
                route = self._execute_node(cycle_id, node, worker_ctx, cycle_ctx)
            except Exception as e:
                log_crash(self.db_path, self.worker, cycle_id, current_node_name, e, worker_ctx, cycle_ctx)
                raise
            # EXIT ends the whole process
            if node.get('type') == 'exit':
                return True
            # END reloops to START internally (same cycle)
            if node.get('type') == 'end':
                apply_scope_resets('END', cycle_ctx, self.scopes)
                start = self.find_start()
                if not start:
                    raise ValueError("END encountered but no START node found to reloop")
                current_node_name = start['name']
                continue
            # Normal edge following
            next_node = follow_edge(current_node_name, route, self.edges)
            # Apply scope trigger if present
            scope_trig = get_scope_trigger(current_node_name, route, self.edges)
            if scope_trig:
                apply_scope_trigger(scope_trig, cycle_ctx, self.scopes)
            dbg = self.debug_getter() if self.debug_getter else None
            if should_pause_after(dbg, node, route):
                from .debug_utils import DebugPause
                raise DebugPause(next_node)
            current_node_name = next_node
        return False

    def _execute_node(self, cycle_id: str, node: Dict, worker_ctx: Dict, cycle_ctx: Dict) -> str:
        name = node['name']
        ntype = node.get('type', 'io')
        handler_kind = node.get('handler')
        started_at = self._utcnow_str()
        # Expose current/executing node
        try:
            from ..db import set_state_kv
            set_state_kv(self.db_path, self.worker, 'current_node', name)
            set_state_kv(self.db_path, self.worker, 'debug.executing_node', name)
        except Exception:
            pass
        begin_step(self.db_path, self.worker, cycle_id, name, handler_kind)
        self._last_step = None
        self._last_ctx_diff = None
        try:
            if ntype == 'start':
                apply_scopes_at_start(cycle_ctx, self.scopes)
                details = {"node": name, "type": ntype, "scopes_applied": len(self.scopes)}
                end_step(self.db_path, self.worker, cycle_id, name, 'succeeded', started_at, details)
                self._last_step = mk_step_summary(details, started_at)
                return 'always'
            if ntype in {'end','exit'}:
                details = {"node": name, "type": ntype}
                end_step(self.db_path, self.worker, cycle_id, name, 'succeeded', started_at, details)
                self._last_step = mk_step_summary(details, started_at)
                return 'always'
            apply_scope_resets(name, cycle_ctx, self.scopes)
            if ntype in {'io','transform'}:
                return self._execute_handler_node(cycle_id, node, worker_ctx, cycle_ctx, started_at)
            if ntype == 'decision':
                return self._execute_decision_node(cycle_id, node, worker_ctx, cycle_ctx, started_at)
            raise ValueError(f"Unknown node type: {ntype}")
        except RetryExhaustedError as e:
            end_step(self.db_path, self.worker, cycle_id, name, 'failed', started_at, {"error": {"message": str(e)[:400], "code": "RETRY_EXHAUSTED", "category": "io"}, "attempts": e.attempts})
            raise
        except Exception as e:
            end_step(self.db_path, self.worker, cycle_id, name, 'failed', started_at, {"error": {"message": str(e)[:400], "code": getattr(e,'code','UNKNOWN'), "category": getattr(e,'category','unknown')}})
            raise
        finally:
            try:
                from ..db import set_state_kv
                set_state_kv(self.db_path, self.worker, 'debug.executing_node', '')
            except Exception:
                pass

    def _execute_handler_node(self, cycle_id: str, node: Dict, worker_ctx: Dict, cycle_ctx: Dict, started_at: str) -> str:
        name = node['name']
        handler = self.registry.get(node.get('handler'))
        inputs = resolve_inputs(node.get('inputs', {}), worker_ctx, cycle_ctx)
        timeout_eff = node.get('timeout_sec', 60)
        if 'timeout' not in inputs and timeout_eff is not None:
            inputs['timeout'] = timeout_eff
        retry_defaults = worker_ctx.get('retry_defaults', {'max': 0, 'delay_sec': 0.5})
        node_retry = node.get('retry', {}) or {}
        retry_policy = {**retry_defaults, **node_retry}
        before_ctx = copy.deepcopy(cycle_ctx)
        attempts = [0]
        def on_retry(attempt, error: HandlerError):
            attempts[0] = attempt
            retry_after = error.details.get('retry_after_sec', retry_policy['delay_sec'] * (2 ** (attempt - 1)))
            log_retry_attempt(self.db_path, self.worker, cycle_id, name, attempt, error.message, error.code, retry_after)
        def execute_handler():
            return handler.run(**inputs)
        outputs = execute_with_retry(execute_handler, retry_policy, on_retry)
        # Extract debug preview if present
        debug_preview = None
        if isinstance(outputs, dict) and '__debug_preview' in outputs:
            debug_preview = outputs.get('__debug_preview')
            try:
                del outputs['__debug_preview']
            except Exception:
                pass
        outputs_spec = node.get('outputs', {})
        if outputs_spec:
            assign_outputs(cycle_ctx, outputs, outputs_spec)
        import json
        details = {"node": name, "type": node.get('type'), "handler_kind": node.get('handler')}
        if attempts[0] > 1:
            details['attempts'] = attempts[0]
        try:
            details['input_size'] = len(json.dumps(inputs))
            details['output_size'] = len(json.dumps(outputs))
        except Exception:
            pass
        if debug_preview is not None:
            details['debug_preview'] = debug_preview
        end_step(self.db_path, self.worker, cycle_id, name, 'succeeded', started_at, details)
        self._last_ctx_diff = compute_ctx_diff(before_ctx, cycle_ctx)
        self._last_step = mk_step_summary(details, started_at)
        return 'always'

    def _execute_decision_node(self, cycle_id: str, node: Dict, worker_ctx: Dict, cycle_ctx: Dict, started_at: str) -> str:
        name = node['name']
        spec = node.get('decision', {})
        kind = spec.get('kind')
        if not kind:
            raise ValueError(f"Decision node {name} missing decision.kind")
        from ..context.resolver import resolve_value
        inp = resolve_value(spec.get('input'), worker_ctx, cycle_ctx)
        routes = get_available_routes(name, self.edges)
        try:
            route = evaluate_decision(kind, inp, spec, routes)
        except DecisionError as e:
            raise ValueError(f"Decision evaluation failed for node {name}: {e}")
        details = {"node": name, "type": "decision", "edge_taken": route, "input_value": str(inp)[:100]}
        end_step(self.db_path, self.worker, cycle_id, name, 'succeeded', started_at, details)
        self._last_step = mk_step_summary(details, started_at)
        self._last_ctx_diff = {"added": {}, "changed": {}, "deleted": []}
        return route

    # Accessors for debug (runner can read last step/diff)
    def get_last_step(self) -> Optional[Dict[str, Any]]:
        return self._last_step
    def get_last_ctx_diff(self) -> Optional[Dict[str, Any]]:
        return self._last_ctx_diff
