




from typing import Dict, Any, List, Set, Tuple
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


def _edges_ok(graph: Dict[str, Any]) -> Tuple[bool, List[str]]:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    subgraphs = graph.get("subgraphs", {})

    # Build node sets per SG
    sg_nodes: Dict[str, Set[str]] = {}
    for n in nodes:
        sg = n.get("subgraph") or "__ROOT__"
        nm = n.get("name")
        if n.get("type") in {"start","end"}:
            continue
        if not nm:
            continue
        sg_nodes.setdefault(sg, set()).add(str(nm))

    errors: List[str] = []

    # Rule: no SG symbolic nodes (only START/END allowed as symbolic)
    for n in nodes:
        if n.get("type") not in {"start","end","step","cond"}:
            errors.append(f"Forbidden symbolic node: {n}")

    # Verify edges point to existing nodes (excluding SG::exit pseudo)
    for e in edges:
        dst = str(e.get("to"))
        if "::" in dst:
            sg, step = dst.split("::", 1)
            if step in {"success","fail","retry","retry_exhausted"}:
                # pseudo node, skip
                continue
            # normal qualified
            if sg not in subgraphs:
                errors.append(f"Edge to unknown subgraph: {dst}")
                continue
            if step not in sg_nodes.get(sg, set()):
                errors.append(f"Edge to unknown node: {dst}")
        else:
            # unqualified: must match some SG entry or a real node in some SG
            found = False
            for sg, entry in subgraphs.items():
                if entry.get("entry") == dst or dst in sg_nodes.get(sg, set()):
                    found = True
                    break
            if not found and dst not in {"START","END"}:
                errors.append(f"Edge to unknown node: {dst}")

    return (len(errors) == 0, errors)


def _unique_labels_per_sg(graph: Dict[str, Any]) -> Tuple[bool, List[str]]:
    nodes = graph.get("nodes", [])
    seen: Dict[str, Set[str]] = {}
    errors: List[str] = []
    for n in nodes:
        if n.get("type") in {"start","end"}:
            continue
        sg = n.get("subgraph") or "__ROOT__"
        nm = str(n.get("name"))
        s = seen.setdefault(sg, set())
        if nm in s:
            errors.append(f"Duplicate step/cond name in subgraph '{sg}': {nm}")
        else:
            s.add(nm)
    return (len(errors) == 0, errors)


def _single_outgoing_for_step(graph: Dict[str, Any]) -> Tuple[bool, List[str]]:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    errors: List[str] = []

    # Count outgoing edges per step (excluding SG::exit)
    out_map: Dict[str, int] = {}
    for e in edges:
        src = str(e.get("from"))
        dst = str(e.get("to"))
        if "::" in dst and dst.split("::",1)[1] in {"success","fail","retry","retry_exhausted"}:
            continue
        out_map[src] = out_map.get(src, 0) + 1

    # Steps must have at most 1 outgoing (conds can have many)
    for n in nodes:
        if n.get("type") != "step":
            continue
        src_name = n.get("name")
        sg = n.get("subgraph")
        qualified = f"{sg}::{src_name}" if sg and src_name else str(src_name)
        if out_map.get(qualified, 0) > 1:
            errors.append(f"Step '{qualified}' has more than one outgoing edge")
    return (len(errors) == 0, errors)


def validate_worker(params: dict) -> dict:
    # Accepts: { operation: 'validate', worker_name, validate: { limit_steps?: int } }
    p = validate_params({**params, "operation": "validate"})
    worker_name = validate_worker_name(p.get("worker_name"))
    worker_root = (PY_WORKERS_DIR / worker_name)
    if not worker_root.exists():
        return {"accepted": False, "status": "error", "message": f"Worker root not found: {worker_name}", "truncated": False}

    # 1) Run controller validations (top-level + steps AST) + extract graph
    try:
        g = validate_and_extract_graph(worker_root)
    except Exception as e:
        return {"accepted": False, "status": "error", "issues": [{"level":"error","code":"VALIDATION_CONTROLLER","message": str(e)[:400]}], "truncated": False}

    issues: List[Dict[str, Any]] = []

    # 2) Count by kinds and per subgraph (for summary)
    counts = _count_nodes_extended(g)

    # 3) Readability rule: enforce limit per subgraph if provided
    limit_steps = 20
    try:
        vcfg = (params or {}).get("validate") or {}
        if isinstance(vcfg, dict) and "limit_steps" in vcfg:
            limit_steps = max(1, min(200, int(vcfg.get("limit_steps"))))
    except Exception:
        pass
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

    # 4) Structural hard rules (blocking)
    ok1, err1 = _unique_labels_per_sg(g)
    for m in err1:
        issues.append({"level":"error","code":"DUPLICATE_LABEL","message": m})

    ok2, err2 = _single_outgoing_for_step(g)
    for m in err2:
        issues.append({"level":"error","code":"STEP_MULTIPLE_OUTGOING","message": m})

    ok3, err3 = _edges_ok(g)
    for m in err3:
        issues.append({"level":"error","code":"EDGE_INVALID","message": m})

    # 5) Derived summary
    accepted = not any(it.get("level") == "error" for it in issues)
    nodes_total = int(counts.get("total_steps", 0)) + int(counts.get("total_conds", 0)) + int((counts.get("types") or {}).get("symbolic", 0))
    nodes_breakdown = dict(counts.get("types", {}))

    return {
        "accepted": accepted,
        "status": ("ok" if accepted else "error"),
        "issues": issues,
        "summary": counts,
        "nodes_total": nodes_total,
        "nodes_breakdown": nodes_breakdown,
        "limit_steps": limit_steps,
        "truncated": False,
    }
