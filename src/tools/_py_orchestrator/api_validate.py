
from typing import Dict, Any, List
from .validators import validate_params, PY_WORKERS_DIR, validate_worker_name
from .controller_parts.graph_build import validate_and_extract_graph


def _count_nodes_extended(graph: Dict[str, Any]) -> Dict[str, Any]:
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
        # Symbolic nodes (START/END)
        if t in {"start", "end"}:
            types["symbolic"] += 1
            continue
        # Conditionals
        if t == "cond":
            total_conds += 1
            types["conds"] += 1
            per_sg[sg]["conds"] += 1
            continue
        # Steps
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
            # If call_kind is missing, we still counted as a step in totals.
            continue
    return {
        "per_subgraph": per_sg,
        "total_steps": total_steps,
        "total_conds": total_conds,
        "types": types,
    }


def validate_worker(params: dict) -> dict:
    # Accepts: { operation: 'validate', worker_name, validate: { limit_steps?: int } }
    p = validate_params({**params, "operation": "validate"})
    worker_name = validate_worker_name(p.get("worker_name"))
    worker_root = (PY_WORKERS_DIR / worker_name)
    if not worker_root.exists():
        return {"accepted": False, "status": "error", "message": f"Worker root not found: {worker_name}", "truncated": False}

    limit_steps = 20
    try:
        vcfg = (params or {}).get("validate") or {}
        if isinstance(vcfg, dict) and "limit_steps" in vcfg:
            try:
                limit_steps = int(vcfg.get("limit_steps"))
            except Exception:
                limit_steps = 20
            if limit_steps <= 0:
                limit_steps = 20
    except Exception:
        pass

    issues: List[Dict[str, Any]] = []

    # 1) Run controller validations (top-level + steps AST) + extract graph
    try:
        g = validate_and_extract_graph(worker_root)
    except Exception as e:
        issues.append({
            "level": "error",
            "code": "VALIDATION_CONTROLLER",
            "message": str(e)[:400]
        })
        return {"accepted": False, "status": "error", "issues": issues, "truncated": False}

    # 2) Count by kinds (symbolic/tool/transform/cond) and per subgraph
    counts = _count_nodes_extended(g)

    # 3) Enforce readability rule: max N steps per subgraph
    per_sg = counts.get("per_subgraph", {})
    for sg, cnt in per_sg.items():
        steps_n = int(cnt.get("steps", 0))
        if steps_n > limit_steps:
            issues.append({
                "level": "error",
                "code": "STEP_LIMIT_EXCEEDED",
                "subgraph": sg,
                "limit": limit_steps,
                "count": steps_n,
                "message": f"Subgraph '{sg}' has {steps_n} steps (> {limit_steps}). Split into smaller subgraphs."
            })

    accepted = not any(it.get("level") == "error" for it in issues)

    # 4) nodes_total = steps + conds + symbolic (align with graph.nodes length)
    nodes_total = int(counts.get("total_steps", 0)) + int(counts.get("total_conds", 0)) + int((counts.get("types") or {}).get("symbolic", 0))

    # Provide a quick top-level mirror
    nodes_breakdown = dict(counts.get("types", {}))

    return {
        "accepted": accepted,
        "status": "ok" if accepted else "error",
        "issues": issues,
        "summary": counts,
        "nodes_total": nodes_total,
        "nodes_breakdown": nodes_breakdown,
        "limit_steps": limit_steps,
        "truncated": False,
    }
