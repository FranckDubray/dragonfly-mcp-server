# Orchestrator - Scopes lifecycle management (<3KB)

from typing import Dict, Any, List
from ..context import reset_scope, seed_scope


def apply_scopes_at_start(cycle_ctx: Dict, scopes: List[Dict]) -> None:
    """
    Apply scope resets at START node.
    
    Args:
        cycle_ctx: Cycle context (modified in-place)
        scopes: Scopes declaration from process
    """
    for scope_def in scopes:
        sname = scope_def.get('name')
        if not sname:
            continue
        reset_on = scope_def.get('reset_on', [])
        seed_data = scope_def.get('seed', {})
        if 'START' in reset_on:
            reset_scope(cycle_ctx, sname)
        if seed_data:
            seed_scope(cycle_ctx, sname, seed_data)


def apply_scope_resets(trigger: str, cycle_ctx: Dict, scopes: List[Dict]) -> None:
    """
    Apply scope resets triggered by node execution or END.
    
    Args:
        trigger: Trigger name (node name, "END", etc.)
        cycle_ctx: Cycle context (modified in-place)
        scopes: Scopes declaration from process
    """
    for scope_def in scopes:
        sname = scope_def.get('name')
        if not sname:
            continue
        if trigger in scope_def.get('reset_on', []):
            reset_scope(cycle_ctx, sname)
            seed_data = scope_def.get('seed', {})
            if seed_data:
                seed_scope(cycle_ctx, sname, seed_data)


def apply_scope_trigger(scope_trigger: Dict, cycle_ctx: Dict, scopes: List[Dict]) -> None:
    """
    Apply scope trigger from edge (enter/leave).
    
    Args:
        scope_trigger: {action: "enter"|"leave", scope: "name"}
        cycle_ctx: Cycle context (modified in-place)
        scopes: Scopes declaration from process
    """
    action = scope_trigger.get('action')
    sname = scope_trigger.get('scope')
    if not sname:
        return
    
    if action == 'enter':
        reset_scope(cycle_ctx, sname)
        for scope_def in scopes:
            if scope_def.get('name') == sname:
                seed_data = scope_def.get('seed', {})
                if seed_data:
                    seed_scope(cycle_ctx, sname, seed_data)
                break
    elif action == 'leave':
        reset_scope(cycle_ctx, sname)
