
from __future__ import annotations
from typing import Dict, Any, List, Tuple
from pathlib import Path

from ..runtime import Process, SubGraphRef
from .validators_toplevel import validate_module_toplevel
from .validators_steps import ast_validate_step
from .errors import ValidationError
from .graph_loader import _load_module_from_path, discover_funcs, _is_process_like, _is_subgraphref_like


def build_graph(worker_root: Path) -> Dict[str, Any]:
    process_path = worker_root / 'process.py'
    validate_module_toplevel(process_path, allowed_assign_names=['PROCESS'])
    if not process_path.is_file():
        raise ValidationError("process.py not found")
    mod = _load_module_from_path(f"pyworker_{worker_root.name}_process", process_path)
    if not hasattr(mod, 'PROCESS'):
        raise ValidationError("PROCESS must be defined as Process(...) in process.py")

    proc = mod.PROCESS
    if not isinstance(proc, Process) and not _is_process_like(proc):
        raise ValidationError("PROCESS must be defined as Process(...) in process.py")

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    subgraphs_order: List[str] = []
    subgraph_infos: Dict[str, Dict[str, Any]] = {}

    def load_sg(ref):
        ref_name = getattr(ref, 'name', None)
        ref_module = getattr(ref, 'module', None)
        if not ref_name or not ref_module:
            return
        sg_path = worker_root / (str(ref_module).replace('.', '/') + '.py')
        validate_module_toplevel(sg_path, allowed_assign_names=['SUBGRAPH'])
        sg_mod = _load_module_from_path(f"pyworker_{worker_root.name}_{ref_name}", sg_path)
        sg = sg_mod.SUBGRAPH
        subgraphs_order.append(sg.name)
        step_names, cond_names = discover_funcs(sg_mod)
        if str(getattr(sg, 'entry', '')) not in (set(step_names) | set(cond_names)):
            raise ValidationError(f"Entry '{sg.entry}' not found in subgraph '{sg.name}' functions")
        if not step_names and not cond_names:
            raise ValidationError(f"No @step/@cond functions found in {sg_path}")
        local_all = set(step_names) | set(cond_names)
        for step_name in step_names:
            nexts, exits, call_kind, call_target = ast_validate_step(sg_path, step_name, kind='step')
            for t in nexts:
                if t not in local_all:
                    raise ValidationError(f"Next target '{t}' in subgraph '{sg.name}' not found among its steps/conds")
            nodes.append({
                "name": step_name,
                "type": "step",
                "subgraph": sg.name,
                "call_kind": call_kind,
                "call_target": call_target,
            })
            for t in nexts:
                edges.append({"from": step_name, "to": t, "when": "always", "subgraph": sg.name})
            for e in exits:
                edges.append({"from": step_name, "to": f"{sg.name}::{e}", "when": e, "subgraph": sg.name})
        for cond_name in cond_names:
            nexts, exits, _, _ = ast_validate_step(sg_path, cond_name, kind='cond')
            for t in nexts:
                if t not in local_all:
                    raise ValidationError(f"Next target '{t}' in subgraph '{sg.name}' not found among its steps/conds")
            nodes.append({"name": cond_name, "type": "cond", "subgraph": sg.name})
            for t in nexts:
                edges.append({"from": cond_name, "to": t, "when": "always", "subgraph": sg.name})
            for e in exits:
                edges.append({"from": cond_name, "to": f"{sg.name}::{e}", "when": e, "subgraph": sg.name})
        next_map = getattr(ref, 'next', {}) or {}
        if getattr(sg, 'parts', None):
            for child in sg.parts:
                load_sg(child)
        subgraph_infos[sg.name] = {"entry": sg.entry, "exits": sg.exits or {}, "next": next_map}

    for ref in (getattr(proc, 'parts', None) or []):
        if isinstance(ref, SubGraphRef) or _is_subgraphref_like(ref):
            load_sg(ref)

    entry_sg = getattr(proc, 'entry', '')
    if entry_sg not in subgraph_infos:
        raise ValidationError(f"Process entry '{entry_sg}' not found among subgraphs")
    edges.append({"from": "START", "to": subgraph_infos[entry_sg]["entry"], "when": "always"})

    names = [getattr(r, 'name', None) for r in (getattr(proc, 'parts', None) or []) if isinstance(r, SubGraphRef) or _is_subgraphref_like(r)]
    names = [n for n in names if n]
    for ref in (getattr(proc, 'parts', None) or []):
        if not (isinstance(ref, SubGraphRef) or _is_subgraphref_like(ref)):
            continue
        nxt = getattr(ref, 'next', {}) or {}
        exits_def = (subgraph_infos.get(ref.name, {}) or {}).get('exits') or {}
        for exit_label, target in nxt.items():
            if exit_label not in exits_def:
                raise ValidationError(f"SubGraphRef '{ref.name}' maps unknown exit label '{exit_label}' (not in SUBGRAPH.exits)")
            if target and target not in names:
                raise ValidationError(f"SubGraphRef '{ref.name}' maps exit '{exit_label}' to unknown subgraph '{target}'")

    for i, sg_name in enumerate(names):
        info = subgraph_infos.get(sg_name, {})
        nxt = info.get('next', {}) or {}
        for exit_label, target in nxt.items():
            target_entry = subgraph_infos.get(target, {}).get('entry')
            if target_entry:
                edges.append({"from": f"{sg_name}::{exit_label}", "to": target_entry, "when": exit_label})
        if 'success' in (info.get('exits') or {}) and i < len(names) - 1 and f"{sg_name}::success" not in [e['from'] for e in edges]:
            next_sg = names[i+1]
            entry_node = subgraph_infos.get(next_sg, {}).get('entry')
            if entry_node:
                edges.append({"from": f"{sg_name}::success", "to": entry_node, "when": "success"})

    if names:
        last = names[-1]
        has_success_out = any(e.get('from') == f"{last}::success" for e in edges)
        if not has_success_out:
            edges.append({"from": f"{last}::success", "to": "END", "when": "success"})

    graph = {
        "nodes": [{"name":"START","type":"start"}] + nodes + [{"name":"END","type":"end"}],
        "edges": edges,
        "metadata": getattr(proc, 'metadata', {}) or {},
        "entry": entry_sg,
        "subgraphs": subgraph_infos,
        "order": names,
    }
    return graph
