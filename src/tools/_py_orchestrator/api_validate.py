




















from typing import Dict, Any, List, Set, Tuple
from .validators import validate_params, PY_WORKERS_DIR, validate_worker_name
from .controller_parts.graph_build import validate_and_extract_graph
from .controller_parts.errors import ValidationError

# NEW: unified validation core
from .validation_core import validate_full


def _count_nodes_extended(graph: Dict[str, Any]) -> Dict[str, Any]:
    # Kept for backward-compat in API shape; the core also computes counts
    nodes = graph.get("nodes", [])
    per_sg: Dict[str, Dict[str, int]] = {}
    types = {"symbolic": 0, "steps_tool": 0, "steps_transform": 0, "conds": 0}
    total_steps = 0
    total_conds = 0

    for n in nodes:
        t = n.get("type")
        sg = n.get("subgraph") or "__ROOT__"
        if sg not in per_sg:
            per_sg[sg] = {"steps": 0, "steps_tool": 0, "steps_transform": 0, "conds": 0}
        if t in {"start", "end"}:
            types["symbolic"] += 1
            continue
        if t == "cond":
            total_conds += 1
            types["conds"] += 1
            per_sg[sg]["conds"] += 1
            continue
        if t == "step":
            total_steps += 1
            per_sg[sg]["steps"] += 1
            ck = n.get("call_kind")
            if ck == "tool":
                types["steps_tool"] += 1
                per_sg[sg]["steps_tool"] += 1
            elif ck == "transform":
                types["steps_transform"] += 1
                per_sg[sg]["steps_transform"] += 1
            continue
    return {
        "per_subgraph": per_sg,
        "total_steps": total_steps,
        "total_conds": total_conds,
        "types": types,
    }


def validate_worker(params: dict) -> dict:
    p = validate_params({**params, "operation": "validate"})
    worker_name = validate_worker_name(p.get("worker_name"))

    # Read new options (all optional; defaults preserve current behavior)
    vcfg = (params or {}).get("validate") or {}
    limit_steps = vcfg.get("limit_steps", 20)
    # DEFAULT CHANGED: include_preflight defaults to True (requested)
    include_preflight = bool(vcfg.get("include_preflight", True))
    strict_tools = vcfg.get("strict_tools", None)
    persist = bool(vcfg.get("persist", False))

    res = validate_full(
        worker_name,
        limit_steps=limit_steps,
        include_preflight=include_preflight,
        strict_tools=strict_tools,
        persist=persist,
    )

    # Keep backward-compat shape: drop heavy graph field from response
    if isinstance(res, dict) and "graph" in res:
        res = dict(res)
        res.pop("graph", None)

    return res
