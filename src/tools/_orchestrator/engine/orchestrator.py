# Orchestrator engine: executes process graph (nodes + edges)

from typing import Dict, Any, Callable, Optional
from ..context import resolve_inputs, assign_outputs, reset_scope, seed_scope
from ..handlers import get_registry, HandlerError
from ..logging import begin_step, end_step
from ..policies import execute_with_retry, RetryExhaustedError
from .decisions import evaluate_decision, DecisionError

class OrchestratorEngine:
    """Generic graph execution engine (no business logic)"""
    
    def __init__(self, graph: Dict, db_path: str, worker: str, cancel_flag_fn: Callable[[], bool]):
        """
        Args:
            graph: Process graph (nodes, edges)
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
    
    def run_cycle(self, cycle_id: str, worker_ctx: Dict, cycle_ctx: Dict) -> None:
        """
        Execute one cycle (START → ... → END).
        
        Args:
            cycle_id: Cycle ID (e.g., "cycle_001")
            worker_ctx: Worker context (read-only)
            cycle_ctx: Cycle context (read/write, modified in-place)
        
        Raises:
            Exception: On fatal error (unhandled)
        """
        # Find START node
        start_node = self._find_start_node()
        if not start_node:
            raise ValueError("No START node found in graph")
        
        # Execute from START
        current_node_name = start_node['name']
        
        while current_node_name and not self.cancel_flag_fn():
            node = self.nodes.get(current_node_name)
            if not node:
                raise ValueError(f"Node not found: {current_node_name}")
            
            # Execute node
            next_route = self._execute_node(cycle_id, node, worker_ctx, cycle_ctx)
            
            # Find next node via edges
            current_node_name = self._follow_edge(current_node_name, next_route)
            
            # If END node reached → break
            if node.get('type') == 'end':
                break
    
    def _find_start_node(self) -> Optional[Dict]:
        """Find START node (type='start')"""
        for node in self.nodes.values():
            if node.get('type') == 'start':
                return node
        return None
    
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
            # START/END nodes: no execution
            if node_type in {'start', 'end'}:
                end_step(self.db_path, self.worker, cycle_id, node_name, 'succeeded', started_at, {
                    "node": node_name,
                    "type": node_type
                })
                return "always"
            
            # IO/transform nodes: execute handler
            if node_type in {'io', 'transform'}:
                return self._execute_handler_node(cycle_id, node, worker_ctx, cycle_ctx, started_at)
            
            # Decision nodes: evaluate condition
            if node_type == 'decision':
                return self._execute_decision_node(cycle_id, node, worker_ctx, cycle_ctx, started_at)
            
            # Unknown node type
            raise ValueError(f"Unknown node type: {node_type}")
        
        except RetryExhaustedError as e:
            # Retry exhausted: log with attempts count
            end_step(self.db_path, self.worker, cycle_id, node_name, 'failed', started_at, {
                "error": {
                    "message": str(e)[:400],
                    "code": "RETRY_EXHAUSTED",
                    "category": "io"
                },
                "attempts": e.attempts
            })
            raise
        
        except Exception as e:
            # Other failure
            end_step(self.db_path, self.worker, cycle_id, node_name, 'failed', started_at, {
                "error": {
                    "message": str(e)[:400],
                    "code": getattr(e, 'code', 'UNKNOWN'),
                    "category": getattr(e, 'category', 'unknown')
                }
            })
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
            # Log retry attempt (optional, for debugging)
            pass
        
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
    
    def _follow_edge(self, from_node: str, route: str) -> Optional[str]:
        """Find next node following edge (from_node + route label)"""
        for edge in self.edges:
            if edge['from'] == from_node:
                when = edge.get('when', 'always')
                if when == route or when == 'always':
                    return edge['to']
        
        # No matching edge found
        return None
    
    @staticmethod
    def _utcnow_str() -> str:
        """UTC ISO8601 microseconds"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')
