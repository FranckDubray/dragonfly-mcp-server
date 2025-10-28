
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Set
from pathlib import Path

# Local transforms registry (Python orchestrator autonomous)
from ..handlers import bootstrap_handlers, get_registry
from .errors import ValidationError

# tool specs root (for existence check)
SPEC_ROOT = Path(__file__).resolve().parents[3] / 'tool_specs'


def _tool_exists(name: str) -> bool:
    if not name:
        return False
    p = SPEC_ROOT / f"{name}.json"
    return p.is_file()


def _collect_calls(graph: Dict[str, Any]) -> Tuple[Set[str], Set[str]]:
    tfs: Set[str] = set()
    tls: Set[str] = set()
    for n in graph.get('nodes', []) or []:
        if n.get('type') != 'step':
            continue
        ck = (n.get('call_kind') or '').strip()
        ct = (n.get('call_target') or '').strip()
        if not ct:
            continue
        if ck == 'transform':
            tfs.add(ct)
        elif ck == 'tool':
            tls.add(ct)
    return tfs, tls


def check_handlers_exist(graph: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Return (missing_transforms, unknown_tools).
    - missing_transforms: blocking (must be empty)
    - unknown_tools: warning by default (tool specs may be missing but server may still support)
    """
    bootstrap_handlers(cancel_flag_fn=None)
    reg = get_registry()
    tfs, tls = _collect_calls(graph)

    # Known built-in transform that is registered later with a cancel-aware instance
    BUILTIN_LATE = {'sleep'}

    missing_tfs: List[str] = []
    for k in sorted(tfs):
        if k in BUILTIN_LATE:
            # Defer to runtime; do not block preflight on sleep
            continue
        if not reg.has(k):
            missing_tfs.append(k)

    unknown_tls: List[str] = []
    for k in sorted(tls):
        # Tools are checked against tool_specs presence only (best-effort)
        if not _tool_exists(k):
            unknown_tls.append(k)
    return missing_tfs, unknown_tls


def _local_graph(graph: Dict[str, Any], sg: str) -> Tuple[Set[str], Dict[str, List[str]]]:
    """Build local node set and adjacency for a subgraph (excluding exit pseudo)."""
    local_nodes: Set[str] = set([n.get('name') for n in (graph.get('nodes') or []) if n.get('subgraph') == sg and n.get('type') in {'step','cond'}])
    adj: Dict[str, List[str]] = {x: [] for x in local_nodes}
    for e in (graph.get('edges') or []):
        if e.get('subgraph') != sg:
            continue
        src = str(e.get('from') or '')
        dst = str(e.get('to') or '')
        if '::' in dst and dst.split('::',1)[1] in {'success','fail','retry','retry_exhausted'}:
            continue
        if src in local_nodes and dst in local_nodes:
            adj[src].append(dst)
    return local_nodes, adj


def _reachable_from_entry(graph: Dict[str, Any], sg: str) -> Set[str]:
    local_nodes, adj = _local_graph(graph, sg)
    entry = ((graph.get('subgraphs') or {}).get(sg) or {}).get('entry') or ''
    if entry not in local_nodes:
        return set()
    seen: Set[str] = set()
    stack = [entry]
    while stack:
        u = stack.pop()
        if u in seen:
            continue
        seen.add(u)
        for v in adj.get(u, []):
            if v not in seen:
                stack.append(v)
    return seen


def check_unreachable(graph: Dict[str, Any]) -> Tuple[Dict[str, List[str]], List[str]]:
    """Return (unreachable_nodes_by_subgraph, unreachable_subgraphs).
    - For each subgraph, list nodes (step/cond) not reachable from its entry.
    - At process level, list subgraphs not reachable from process entry (using edges between subgraphs already built).
    """
    subgraphs = graph.get('subgraphs') or {}
    order = graph.get('order') or []

    # Nodes unreachable per subgraph
    unreachable_by_sg: Dict[str, List[str]] = {}
    for sg in subgraphs.keys():
        all_nodes = [n.get('name') for n in (graph.get('nodes') or []) if n.get('subgraph') == sg and n.get('type') in {'step','cond'}]
        reach = _reachable_from_entry(graph, sg)
        dead = [x for x in all_nodes if x not in reach]
        if dead:
            unreachable_by_sg[sg] = dead

    # Subgraph-level reachability: use the built edges between subgraphs
    # Build graph of SG via edges from "SG::exit" -> entry(target)
    sg_adj: Dict[str, Set[str]] = {sg: set() for sg in order}
    for e in (graph.get('edges') or []):
        src = str(e.get('from') or '')
        dst = str(e.get('to') or '')
        if '::' in src:
            sg_src, exit_label = src.split('::', 1)
            # Only consider success/fail/retry/... edges that connect to another subgraph entry
            if dst and '::' not in dst:
                # find which subgraph has this entry
                for sg, info in subgraphs.items():
                    if info.get('entry') == dst:
                        if sg_src in sg_adj:
                            sg_adj[sg_src].add(sg)
                        break
    entry_sg = graph.get('entry') or (order[0] if order else '')
    seen_sg: Set[str] = set()
    if entry_sg:
        stack = [entry_sg]
        while stack:
            u = stack.pop()
            if u in seen_sg:
                continue
            seen_sg.add(u)
            for v in sg_adj.get(u, set()):
                if v not in seen_sg:
                    stack.append(v)
    unreachable_sg = [sg for sg in order if sg not in seen_sg]

    return unreachable_by_sg, unreachable_sg


def run_all_checks(graph: Dict[str, Any], *, strict_tools: bool = False) -> Tuple[List[str], List[str]]:
    """Run all controller-level checks. Return (errors, warnings).
    Errors are blockers; warnings are informational.
    - Missing transforms -> error (except known built-ins like 'sleep')
    - Unknown tools (no spec) -> warning (unless strict_tools)
    - Unreachable nodes -> error
    - Unreachable subgraphs -> error
    """
    errors: List[str] = []
    warnings: List[str] = []

    missing_tfs, unknown_tls = check_handlers_exist(graph)
    if missing_tfs:
        errors.append("Missing transforms: " + ", ".join(sorted(missing_tfs)))
    if unknown_tls:
        msg = "Unknown tools (no tool_specs/*.json found): " + ", ".join(sorted(unknown_tls))
        if strict_tools:
            errors.append(msg)
        else:
            warnings.append(msg)

    unr_nodes, unr_sg = check_unreachable(graph)
    if unr_nodes:
        for sg, nodes in unr_nodes.items():
            errors.append(f"Unreachable nodes in subgraph '{sg}': {', '.join(nodes)}")
    if unr_sg:
        errors.append("Unreachable subgraphs from process entry: " + ", ".join(unr_sg))

    return errors, warnings
