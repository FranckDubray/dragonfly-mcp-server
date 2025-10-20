# Orchestrator engine — common helpers for node execution
from typing import Dict, Optional
from ..logging import begin_step, end_step
from .orchestrator_scopes import apply_scopes_at_start, apply_scope_resets
from ..utils import utcnow_str


def begin_node(core, cycle_id: str, node: Dict) -> str:
    name = node['name']
    handler_kind = node.get('handler')
    begin_step(core.db_path, core.worker, cycle_id, name, handler_kind)
    return utcnow_str()


def exec_start_node(core, cycle_id: str, node: Dict, cycle_ctx: Dict) -> str:
    name = node['name']
    apply_scopes_at_start(cycle_ctx, core.scopes)
    details = {"node": name, "type": 'start', "scopes_applied": len(core.scopes)}
    end_step(core.db_path, core.worker, cycle_id, name, 'succeeded', utcnow_str(), details)
    return 'always'


def exec_end_or_exit_node(core, cycle_id: str, node: Dict) -> str:
    name = node['name']
    details = {"node": name, "type": node.get('type')}
    end_step(core.db_path, core.worker, cycle_id, name, 'succeeded', utcnow_str(), details)
    return 'always'


def apply_resets_before(core, node: Dict, cycle_ctx: Dict) -> None:
    apply_scope_resets(node['name'], cycle_ctx, core.scopes)
