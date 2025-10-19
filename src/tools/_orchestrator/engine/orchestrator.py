# Orchestrator engine: executes process graph (nodes + edges)

from typing import Dict, Any, Callable, Optional
from ..context import resolve_inputs, assign_outputs, reset_scope, seed_scope
from ..handlers import get_registry, HandlerError
from ..logging import begin_step, end_step, log_retry_attempt
from ..logging.crash_logger import log_crash
from ..policies import execute_with_retry, RetryExhaustedError
from .decisions import evaluate_decision, DecisionError

class OrchestratorEngine:
    """Generic graph execution engine (no business logic)"""
    
    # Safety guard: max nodes per cycle (prevents infinite loops within a cycle)
    MAX_NODES_PER_CYCLE = 100
    
    def __init__(self, graph: Dict, db_path: str, worker: str, cancel_flag_fn: Callable[[], bool]):
        """
        Args:
            graph: Process graph (nodes, edges, scopes)
            db_path: SQLite DB path (for logging)
            worker: Worker name
            cancel_flag_fn: Callable that returns True if canceled
        """
        self.graph = graph
        self.db_path = db_path
        self.worker = worker
        self.cancel_flag_fn = cancel_flag_fn
        self.registry = get_registry()
        
        # Parse graph
        self.nodes = {n['name']: n for n in graph.get('nodes', [])}
        self.edges = graph.get('edges', [])
        self.scopes = graph.get('scopes', [])
    
    def run_cycle(self, cycle_id: str, worker_ctx: Dict, cycle_ctx: Dict) -> bool:
        """
        Execute one cycle (START → ... → END/EXIT).
        
        Args:
            cycle_id: Cycle ID (e.g., "cycle_001")
            worker_ctx: Worker context (read-only)
            cycle_ctx: Cycle context (read/write, modified in-place)
        
        Returns:
            bool: True if EXIT node reached (stop worker), False if END node (continue loop)
        
        Raises:
            Exception: On fatal error (unhandled)
        """
        # Find START node
        start_node = self._find_start_node()
        if not start_node:
            raise ValueError("No START node found in graph")
        
        # Execute from START with safety guard
        current_node_name = start_node['name']
        nodes_traversed = 0
        
        while current_node_name and not self.cancel_flag_fn():
            # Safety guard: prevent infinite loops within a cycle
            nodes_traversed += 1
            if nodes_traversed > self.MAX_NODES_PER_CYCLE:
                error = RuntimeError(
                    f"Cycle {cycle_id}: {nodes_traversed} nodes traversed "
                    f"(max: {self.MAX_NODES_PER_CYCLE}) - infinite loop detected. "
                    f"Check your graph for missing exit conditions in retry loops."
                )
                # Log crash with context snapshot
                log_crash(self.db_path, self.worker, cycle_id, current_node_name, error, worker_ctx, cycle_ctx)
                raise error
            
            node = self.nodes.get(current_node_name)
            if not node:
                raise ValueError(f"Node not found: {current_node_name}")
            
            # Execute node (with crash logging on fatal errors)
            try:
                next_route = self._execute_node(cycle_id, node, worker_ctx, cycle_ctx)
            except Exception as e:
                # Log crash with full context
                log_crash(self.db_path, self.worker, cycle_id, current_node_name, e, worker_ctx, cycle_ctx)
                raise  # Re-raise to stop cycle
            
            # Check if EXIT node reached
            if node.get('type') == 'exit':
                return True  # Signal to stop worker
            
            # If END node reached → apply scope resets, then continue loop
            if node.get('type') == 'end':
                self._apply_scope_resets('END', cycle_ctx)
                return False  # Signal to continue to next cycle
            
            # Find next node via edges (with scope triggers)
            next_node_name = self._follow_edge_with_triggers(current_node_name, next_route, cycle_ctx)
            current_node_name = next_node_name
        
        # Loop exited without reaching END/EXIT (cancel or error)
        return False
    
    def _find_start_node(self) -> Optional[Dict]:
        """Find START node (type='start')"""
        for node in self.nodes.values():
            if node.get('type') == 'start':
                return node
        return None
    
    def _apply_scopes_at_start(self, cycle_ctx: Dict) -> None:
        """
        Apply scope resets and seeds at START node.
        
        Reads graph.scopes[] and for each scope:
        - If 'START' in reset_on → reset (clear) the scope
        - If seed data present → seed the scope
        
        Args:
            cycle_ctx: Cycle context (modified in-place)
        """
        for scope_def in self.scopes:
            scope_name = scope_def.get('name')
            if not scope_name:
                continue
            
            reset_on = scope_def.get('reset_on', [])
            seed_data = scope_def.get('seed', {})
            
            # Reset if START in reset_on list
            if 'START' in reset_on:
                reset_scope(cycle_ctx, scope_name)
            
            # Seed (always apply if seed_data present)
            if seed_data:
                seed_scope(cycle_ctx, scope_name, seed_data)
    
    def _apply_scope_resets(self, trigger: str, cycle_ctx: Dict) -> None:
        """
        Apply scope resets for a trigger (e.g., 'END', node name).
        
        Args:
            trigger: Trigger name ('START', 'END', or node name)
            cycle_ctx: Cycle context (modified in-place)
        """
        for scope_def in self.scopes:
            scope_name = scope_def.get('name')
            if not scope_name:
                continue
            
            reset_on = scope_def.get('reset_on', [])
            
            if trigger in reset_on:
                reset_scope(cycle_ctx, scope_name)
                
                # Re-seed if seed data present
                seed_data = scope_def.get('seed', {})
                if seed_data:
                    seed_scope(cycle_ctx, scope_name, seed_data)
    
    def _apply_scope_trigger(self, scope_trigger: Dict, cycle_ctx: Dict) -> None:
        """
        Apply scope trigger from edge (enter/leave).
        
        Args:
            scope_trigger: Edge scope_trigger dict {"action": "enter"|"leave", "scope": "name"}
            cycle_ctx: Cycle context (modified in-place)
        """
        action = scope_trigger.get('action')
        scope_name = scope_trigger.get('scope')
        
        if not scope_name:
            return
        
        if action == 'enter':
            # Enter: reset + seed
            reset_scope(cycle_ctx, scope_name)
            
            # Find seed data from scope definition
            for scope_def in self.scopes:
                if scope_def.get('name') == scope_name:
                    seed_data = scope_def.get('seed', {})
                    if seed_data:
                        seed_scope(cycle_ctx, scope_name, seed_data)
                    break
        
        elif action == 'leave':
            # Leave: reset (clear)
            reset_scope(cycle_ctx, scope_name)
    
    def _execute_node(self, cycle_id: str, node: Dict, worker_ctx: Dict, cycle_ctx: Dict) -> str:
        """
        Execute a single node.
        
        Args:
            cycle_id: Cycle ID
            node: Node dict
            worker_ctx: Worker context
            cycle_ctx: Cycle context
        
        Returns:
            Route label (e.g., "always", "true", "false", "SPAM")
        """
        node_name = node['name']
        node_type = node.get('type', 'io')
        handler_kind = node.get('handler')
        
        started_at = self._utcnow_str()
        begin_step(self.db_path, self.worker, cycle_id, node_name, handler_kind)
        
        try:
            # START node: apply scopes before returning
            if node_type == 'start':
                self._apply_scopes_at_start(cycle_ctx)
                end_step(self.db_path, self.worker, cycle_id, node_name, 'succeeded', started_at, {
                    "node": node_name,
                    "type": node_type,
                    "scopes_applied": len(self.scopes)
                })
                return "always"
            
            # END/EXIT nodes: no execution (scopes handled in run_cycle)
            if node_type in {'end', 'exit'}:
                end_step(self.db_path, self.worker, cycle_id, node_name, 'succeeded', started_at, {
                    "node": node_name,
                    "type": node_type
                })
                return "always"
            
            # Check if this node triggers scope resets (custom node triggers)
            self._apply_scope_resets(node_name, cycle_ctx)
            
            # IO/transform nodes: execute handler
            if node_type in {'io', 'transform'}:
                return self._execute_handler_node(cycle_id, node, worker_ctx, cycle_ctx, started_at)
            
            # Decision nodes: evaluate condition
            if node_type == 'decision':
                return self._execute_decision_node(cycle_id, node, worker_ctx, cycle_ctx, started_at)
            
            # Unknown node type
            raise ValueError(f"Unknown node type: {node_type}")
        
        except RetryExhaustedError as e:
            # Retry exhausted: log with attempts count + crash log
            end_step(self.db_path, self.worker, cycle_id, node_name, 'failed', started_at, {
                "error": {
                    "message": str(e)[:400],
                    "code": "RETRY_EXHAUSTED",
                    "category": "io"
                },
                "attempts": e.attempts
            })
            # Crash log already done in run_cycle, just re-raise
            raise
        
        except Exception as e:
            # Other failure: log + crash log
            end_step(self.db_path, self.worker, cycle_id, node_name, 'failed', started_at, {
                "error": {
                    "message": str(e)[:400],
                    "code": getattr(e, 'code', 'UNKNOWN'),
                    "category": getattr(e, 'category', 'unknown')
                }
            })
            # Crash log already done in run_cycle, just re-raise
            raise
    
    def _execute_handler_node(self, cycle_id: str, node: Dict, worker_ctx: Dict, cycle_ctx: Dict, started_at: str) -> str:
        """Execute io/transform node (call handler with retry)"""
        node_name = node['name']
        handler_kind = node.get('handler')
        
        if not handler_kind:
            raise ValueError(f"Node {node_name} missing handler")
        
        # Get handler
        handler = self.registry.get(handler_kind)
        
        # Resolve inputs
        inputs_spec = node.get('inputs', {})
        inputs = resolve_inputs(inputs_spec, worker_ctx, cycle_ctx)
        
        # Get retry policy (default: no retry)
        retry_policy = node.get('retry', {'max': 0, 'delay_sec': 0.5})
        
        # Define handler execution function
        def execute_handler():
            return handler.run(**inputs)
        
        # Execute with retry
        attempts_count = [0]  # Mutable for closure
        
        def on_retry(attempt: int, error: HandlerError):
            attempts_count[0] = attempt
            # Log retry attempt to DB
            retry_after = error.details.get('retry_after_sec', retry_policy['delay_sec'] * (2 ** (attempt - 1)))
            log_retry_attempt(
                self.db_path,
                self.worker,
                cycle_id,
                node_name,
                attempt,
                error.message,
                error.code,
                retry_after
            )
        
        outputs = execute_with_retry(execute_handler, retry_policy, on_retry)
        
        # Map outputs to cycle_ctx
        outputs_spec = node.get('outputs', {})
        if outputs_spec:
            assign_outputs(cycle_ctx, outputs, outputs_spec)
        
        # Log success (with attempts if retried)
        details = {
            "node": node_name,
            "type": node.get('type'),
            "handler_kind": handler_kind
        }
        if attempts_count[0] > 1:
            details['attempts'] = attempts_count[0]
        
        end_step(self.db_path, self.worker, cycle_id, node_name, 'succeeded', started_at, details)
        
        return "always"
    
    def _execute_decision_node(self, cycle_id: str, node: Dict, worker_ctx: Dict, cycle_ctx: Dict, started_at: str) -> str:
        """Execute decision node (evaluate condition)"""
        node_name = node['name']
        decision_spec = node.get('decision', {})
        kind = decision_spec.get('kind')
        
        if not kind:
            raise ValueError(f"Decision node {node_name} missing decision.kind")
        
        # Resolve input path
        input_path_raw = decision_spec.get('input')
        if not input_path_raw:
            raise ValueError(f"Decision node {node_name} missing decision.input")
        
        # Resolve value
        from ..context.resolver import resolve_value
        input_value = resolve_value(input_path_raw, worker_ctx, cycle_ctx)
        
        # Get available routes for this decision node
        available_routes = self._get_available_routes(node_name)
        
        # Evaluate decision (via decisions module)
        try:
            route = evaluate_decision(kind, input_value, decision_spec, available_routes)
        except DecisionError as e:
            raise ValueError(f"Decision evaluation failed for node {node_name}: {e}")
        
        # Log decision
        end_step(self.db_path, self.worker, cycle_id, node_name, 'succeeded', started_at, {
            "node": node_name,
            "type": "decision",
            "edge_taken": route,
            "input_value": str(input_value)[:100]  # Truncate for logging
        })
        
        return route
    
    def _get_available_routes(self, from_node: str) -> list:
        """Get available route labels for a node (from edges)"""
        routes = []
        for edge in self.edges:
            if edge['from'] == from_node:
                when = edge.get('when', 'always')
                if when != 'always':
                    routes.append(when)
        return routes
    
    def _follow_edge_with_triggers(self, from_node: str, route: str, cycle_ctx: Dict) -> Optional[str]:
        """
        Find next node following edge (from_node + route label) and apply scope triggers.
        
        Args:
            from_node: Source node name
            route: Route label
            cycle_ctx: Cycle context (for scope triggers)
        
        Returns:
            Next node name or None
        """
        for edge in self.edges:
            if edge['from'] == from_node:
                when = edge.get('when', 'always')
                if when == route or when == 'always':
                    # Apply scope trigger if present
                    scope_trigger = edge.get('scope_trigger')
                    if scope_trigger:
                        self._apply_scope_trigger(scope_trigger, cycle_ctx)
                    
                    return edge['to']
        
        # No matching edge found
        return None
    
    @staticmethod
    def _utcnow_str() -> str:
        """UTC ISO8601 microseconds"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')
