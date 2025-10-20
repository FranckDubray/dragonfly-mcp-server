
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timezone
from ..context import resolve_inputs, assign_outputs, reset_scope, seed_scope
from ..handlers import get_registry, HandlerError
from ..logging import begin_step, end_step, log_retry_attempt
from ..logging.crash_logger import log_crash
from ..policies import execute_with_retry, RetryExhaustedError
from .decisions import evaluate_decision, DecisionError
from .debug_utils import DebugPause, compute_ctx_diff, mk_step_summary, should_pause_after
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
            # Handle EXIT / END semantics here (no runner-driven sleep)
            if node.get('type') == 'exit':
                return True  # EXIT ends the whole process
            if node.get('type') == 'end':
                # Declarative resets for END, then reloop to START automatically
                self._apply_scope_resets('END', cycle_ctx)
                start = self.find_start()
                if not start:
                    raise ValueError("END encountered but no START node found to reloop")
                current_node_name = start['name']
                # Continue same cycle (no cycle_id increment here)
                continue
            # Normal edge following
            next_node = self._follow_edge_with_triggers(current_node_name, route, cycle_ctx)
            dbg = self.debug_getter() if self.debug_getter else None
            if should_pause_after(dbg, node, route):
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
                self._apply_scopes_at_start(cycle_ctx)
                details = {"node": name, "type": ntype, "scopes_applied": len(self.scopes)}
                end_step(self.db_path, self.worker, cycle_id, name, 'succeeded', started_at, details)
                self._last_step = mk_step_summary(details, started_at)
                return 'always'
            if ntype in {'end','exit'}:
                details = {"node": name, "type": ntype}
                end_step(self.db_path, self.worker, cycle_id, name, 'succeeded', started_at, details)
                self._last_step = mk_step_summary(details, started_at)
                return 'always'
            self._apply_scope_resets(name, cycle_ctx)
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
        # Retry policy: merge worker_ctx.retry_defaults with node.retry (node overrides)
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
        outputs_spec = node.get('outputs', {})
        if outputs_spec:
            assign_outputs(cycle_ctx, outputs, outputs_spec)
        # Enrich details
        import json
        details = {"node": name, "type": node.get('type'), "handler_kind": node.get('handler')}
        if attempts[0] > 1:
            details['attempts'] = attempts[0]
        try:
            details['input_size'] = len(json.dumps(inputs))
            details['output_size'] = len(json.dumps(outputs))
        except Exception:
            pass
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
        routes = self._get_available_routes(name)
        try:
            route = evaluate_decision(kind, inp, spec, routes)
        except DecisionError as e:
            raise ValueError(f"Decision evaluation failed for node {name}: {e}")
        details = {"node": name, "type": "decision", "edge_taken": route, "input_value": str(inp)[:100]}
        end_step(self.db_path, self.worker, cycle_id, name, 'succeeded', started_at, details)
        self._last_step = mk_step_summary(details, started_at)
        self._last_ctx_diff = {"added": {}, "changed": {}, "deleted": []}
        return route

    def _apply_scopes_at_start(self, cycle_ctx: Dict) -> None:
        for scope_def in self.scopes:
            sname = scope_def.get('name')
            if not sname:
                continue
            reset_on = scope_def.get('reset_on', [])
            seed_data = scope_def.get('seed', {})
            if 'START' in reset_on:
                reset_scope(cycle_ctx, sname)
            if seed_data:
                seed_scope(cycle_ctx, sname, seed_data)

    def _apply_scope_resets(self, trigger: str, cycle_ctx: Dict) -> None:
        for scope_def in self.scopes:
            sname = scope_def.get('name')
            if not sname:
                continue
            if trigger in scope_def.get('reset_on', []):
                reset_scope(cycle_ctx, sname)
                seed_data = scope_def.get('seed', {})
                if seed_data:
                    seed_scope(cycle_ctx, sname, seed_data)

    def _get_available_routes(self, from_node: str) -> list:
        routes = []
        for edge in self.edges:
            if edge['from'] == from_node:
                when = edge.get('when', 'always')
                if when != 'always':
                    routes.append(when)
        return routes

    def _follow_edge_with_triggers(self, from_node: str, route: str, cycle_ctx: Dict) -> Optional[str]:
        for edge in self.edges:
            if edge['from'] == from_node:
                when = edge.get('when', 'always')
                if when == route or when == 'always':
                    scope_trigger = edge.get('scope_trigger')
                    if scope_trigger:
                        self._apply_scope_trigger(scope_trigger, cycle_ctx)
                    return edge['to']
        return None

    def _apply_scope_trigger(self, scope_trigger: Dict, cycle_ctx: Dict) -> None:
        action = scope_trigger.get('action')
        sname = scope_trigger.get('scope')
        if not sname:
            return
        if action == 'enter':
            reset_scope(cycle_ctx, sname)
            for scope_def in self.scopes:
                if scope_def.get('name') == sname:
                    seed_data = scope_def.get('seed', {})
                    if seed_data:
                        seed_scope(cycle_ctx, sname, seed_data)
                    break
        elif action == 'leave':
            reset_scope(cycle_ctx, sname)

    # Accessors for debug (runner can read last step/diff)
    def get_last_step(self) -> Optional[Dict[str, Any]]:
        return self._last_step
    def get_last_ctx_diff(self) -> Optional[Dict[str, Any]]:
        return self._last_ctx_diff
