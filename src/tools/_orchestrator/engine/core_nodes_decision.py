








# Orchestrator engine — decision node execution
from typing import Dict
from ..logging import end_step
from .decisions import evaluate_decision, DecisionError
from .debug_utils import _preview, is_truncated_preview, mk_step_summary
from ..context.resolver import resolve_value
from .orchestrator_edges import get_available_routes


def execute_decision_node(core, cycle_id: str, node: Dict, worker_ctx: Dict, cycle_ctx: Dict, started_at: str) -> str:
    name = node['name']
    spec = node.get('decision', {})
    kind = spec.get('kind')
    if not kind:
        raise ValueError(f"Decision node {name} missing decision.kind")

    # Resolve input explicitly
    inp = resolve_value(spec.get('input'), worker_ctx, cycle_ctx)
    # Resolve the whole spec (to allow dynamic 'value' and others)
    # This preserves existing behavior while enabling ${...} in decision fields (e.g., compare.value)
    spec_resolved = resolve_value(spec, worker_ctx, cycle_ctx)

    routes = get_available_routes(name, core.edges)

    try:
        route = evaluate_decision(kind, inp, spec_resolved, routes)
    except DecisionError as e:
        raise ValueError(f"Decision evaluation failed for node {name}: {e}")

    details = {"node": name, "type": "decision", "edge_taken": route, "input_value": str(inp)[:100]}

    try:
        decision_inputs = {"decision": {"kind": kind, "spec": spec_resolved}, "input_resolved": inp, "available_routes": routes}
        decision_outputs = {"route": route}
        dp = {"inputs": _preview(decision_inputs), "output": _preview(decision_outputs)}
        details['debug_preview'] = dp
        if is_truncated_preview(dp):
            details['truncated'] = True
    except Exception:
        pass

    end_step(core.db_path, core.worker, cycle_id, name, 'succeeded', started_at, details)

    # Update debug summary for pause/inspect
    core._last_step = mk_step_summary(details, started_at, inputs=decision_inputs, outputs=decision_outputs, cycle_ctx=cycle_ctx)
    core._last_ctx_diff = {"added": {}, "changed": {}, "deleted": []}

    return route
