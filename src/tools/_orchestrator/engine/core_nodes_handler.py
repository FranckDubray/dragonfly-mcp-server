# Orchestrator engine — handler node execution (JSON in → JSON out)
from typing import Dict
import copy
import json
from ..context import resolve_inputs, assign_outputs
from ..handlers import HandlerError
from ..policies import execute_with_retry
from ..logging import end_step, log_retry_attempt
from .debug_utils import compute_ctx_diff, mk_step_summary, is_truncated_preview


def execute_handler_node(core, cycle_id: str, node: Dict, worker_ctx: Dict, cycle_ctx: Dict, started_at: str) -> str:
    """Execute an IO/transform node via registered handler."""
    name = node['name']
    handler = core.registry.get(node.get('handler'))

    # Resolve inputs
    inputs = resolve_inputs(node.get('inputs', {}), worker_ctx, cycle_ctx)

    # Timeout propagation
    timeout_eff = node.get('timeout_sec', 60)
    if 'timeout' not in inputs and timeout_eff is not None:
        inputs['timeout'] = timeout_eff

    # Retry policy (defaults from worker_ctx overrideable per node)
    retry_defaults = worker_ctx.get('retry_defaults', {'max': 0, 'delay_sec': 0.5})
    node_retry = node.get('retry', {}) or {}
    retry_policy = {**retry_defaults, **node_retry}

    before_ctx = copy.deepcopy(cycle_ctx)
    attempts = [0]

    def on_retry(attempt, error: HandlerError):
        attempts[0] = attempt
        retry_after = error.details.get('retry_after_sec', retry_policy['delay_sec'] * (2 ** (attempt - 1)))
        log_retry_attempt(core.db_path, core.worker, cycle_id, name, attempt, error.message, error.code, retry_after)

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

    # Map outputs → cycle_ctx
    outputs_spec = node.get('outputs', {})
    if outputs_spec:
        assign_outputs(cycle_ctx, outputs, outputs_spec)

    # Log step end (sizes, attempts, debug)
    details = {"node": name, "type": node.get('type'), "handler_kind": node.get('handler')}
    try:
        details['input_size'] = len(json.dumps(inputs))
        details['output_size'] = len(json.dumps(outputs))
    except Exception:
        pass
    if attempts[0] > 1:
        details['attempts'] = attempts[0]
    if debug_preview is not None:
        details['debug_preview'] = debug_preview
        if is_truncated_preview(debug_preview):
            details['truncated'] = True

    end_step(core.db_path, core.worker, cycle_id, name, 'succeeded', started_at, details)

    # Update debug summaries on core (for pause/inspect)
    core._last_ctx_diff = compute_ctx_diff(before_ctx, cycle_ctx)
    core._last_step = mk_step_summary(details, started_at, inputs=inputs, outputs=outputs, cycle_ctx=cycle_ctx)

    return 'always'
