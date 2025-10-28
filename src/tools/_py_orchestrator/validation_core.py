from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import json as _json
import os

from .validators import PY_WORKERS_DIR
from .controller_parts.graph_build import validate_and_extract_graph
from .controller_parts.errors import ValidationError
from .controller_parts.graph_checks import run_all_checks
from .api_spawn import db_path_for_worker
from .db import set_state_kv, set_phase
from .logging.crash_logger import log_crash

# --- Helpers copied (light) from api_validate ---------------------------------

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

    sg_nodes: Dict[str, set] = {}
    for n in nodes:
        sg = n.get("subgraph") or "__ROOT__"
        nm = n.get("name")
        if n.get("type") in {"start", "end"}:
            continue
        if not nm:
            continue
        sg_nodes.setdefault(sg, set()).add(str(nm))

    errors: List[str] = []

    for n in nodes:
        if n.get("type") not in {"start", "end", "step", "cond"}:
            errors.append(f"Forbidden symbolic node: {n}")

    for e in edges:
        dst = str(e.get("to"))
        if "::" in dst:
            sg, step = dst.split("::", 1)
            if step in {"success", "fail", "retry", "retry_exhausted"}:
                continue
            if sg not in subgraphs:
                errors.append(f"Edge to unknown subgraph: {dst}")
                continue
            if step not in sg_nodes.get(sg, set()):
                errors.append(f"Edge to unknown node: {dst}")
        else:
            found = False
            for sg, info in subgraphs.items():
                if info.get("entry") == dst or dst in sg_nodes.get(sg, set()):
                    found = True
                    break
            if not found and dst not in {"START", "END"}:
                errors.append(f"Edge to unknown node: {dst}")

    return (len(errors) == 0, errors)


def _unique_labels_per_sg(graph: Dict[str, Any]) -> Tuple[bool, List[str]]:
    nodes = graph.get("nodes", [])
    seen: Dict[str, set] = {}
    errors: List[str] = []
    for n in nodes:
        if n.get("type") in {"start", "end"}:
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

    out_map: Dict[str, int] = {}
    for e in edges:
        src = str(e.get("from"))
        dst = str(e.get("to"))
        if "::" in dst and dst.split("::", 1)[1] in {"success", "fail", "retry", "retry_exhausted"}:
            continue
        out_map[src] = out_map.get(src, 0) + 1

    for n in nodes:
        if n.get("type") != "step":
            continue
        src_name = n.get("name")
        sg = n.get("subgraph")
        qualified = f"{sg}::{src_name}" if sg and src_name else str(src_name)
        if out_map.get(qualified, 0) > 1:
            errors.append(f"Step '{qualified}' has more than one outgoing edge")
    return (len(errors) == 0, errors)

# --- Strict tools resolver ---------------------------------------------------

def _env_truthy(name: str) -> bool:
    try:
        v = os.getenv(name)
        if v is None:
            return False
        s = str(v).strip().lower()
        return s in {"1","true","yes","on"}
    except Exception:
        return False


def _resolve_strict_tools(graph: Optional[Dict[str, Any]], override: Optional[bool]) -> bool:
    if override is not None:
        return bool(override)
    try:
        if _env_truthy('PY_ORCH_STRICT_TOOLS'):
            return True
    except Exception:
        pass
    try:
        if isinstance(graph, dict):
            return bool((graph.get('metadata') or {}).get('strict_tools'))
    except Exception:
        pass
    return False

# --- Public core -------------------------------------------------------------

def validate_full(worker_name: str, *, limit_steps: int = 20,
                  include_preflight: bool = False,
                  strict_tools: Optional[bool] = None,
                  persist: bool = False) -> Dict[str, Any]:
    """Unified validation core.
    - Returns compile-time issues and (optional) preflight checks.
    - When persist=True, applies the same KV side effects as preflight.
    """
    worker_root = (PY_WORKERS_DIR / worker_name)
    dbp = db_path_for_worker(worker_name)

    if not worker_root.exists():
        res = {"accepted": False, "status": "error", "issues": [{"level":"error","code":"WORKER_ROOT","message": f"Worker root not found: {worker_name}"}], "truncated": False}
        if persist:
            try:
                set_state_kv(dbp, worker_name, 'last_error', f"Worker root not found: {worker_name}")
                set_phase(dbp, worker_name, 'failed')
            except Exception:
                pass
        return res

    # Extract graph (may raise AST ValidationError)
    try:
        graph = validate_and_extract_graph(worker_root)
    except ValidationError as ve:
        issue = {"level":"error","code": ve.code or "VALIDATION_CONTROLLER","message": str(ve)}
        if getattr(ve, 'file', None):
            issue["file"] = ve.file
        if getattr(ve, 'line', None) is not None:
            issue["line"] = ve.line
        if getattr(ve, 'rule', None):
            issue["rule"] = ve.rule
        if getattr(ve, 'fix', None):
            issue["fix"] = ve.fix
        if getattr(ve, 'example', None):
            issue["example"] = ve.example
        if persist:
            try:
                set_phase(dbp, worker_name, 'failed')
                set_state_kv(dbp, worker_name, 'last_error', (str(ve)[:300]))
                log_crash(dbp, worker_name, cycle_id='startup', node='controller_validate', error=ve, worker_ctx={}, cycle_ctx={})
            except Exception:
                pass
        return {"accepted": False, "status": "error", "issues": [issue], "truncated": False}
    except Exception as e:
        if persist:
            try:
                set_phase(dbp, worker_name, 'failed')
                set_state_kv(dbp, worker_name, 'last_error', f"Unexpected preflight error: {str(e)[:300]}")
                log_crash(dbp, worker_name, cycle_id='startup', node='controller_validate', error=e, worker_ctx={}, cycle_ctx={})
            except Exception:
                pass
        return {"accepted": False, "status": "error", "issues": [{"level":"error","code":"VALIDATION_CONTROLLER","message": str(e)[:400]}], "truncated": False}

    # Compile-time checks (structure)
    issues: List[Dict[str, Any]] = []
    counts = _count_nodes_extended(graph)

    # Readability limit per subgraph
    try:
        l = int(limit_steps)
        if l < 1:
            l = 1
        if l > 200:
            l = 200
        limit_steps = l
    except Exception:
        limit_steps = 20

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
                "message": f"Subgraph '{sg}' has {steps_n} steps (> {limit_steps}). Split into smaller subgraphs.",
            })

    ok1, err1 = _unique_labels_per_sg(graph)
    for m in err1:
        issues.append({"level":"error","code":"DUPLICATE_LABEL","message": m})

    ok2, err2 = _single_outgoing_for_step(graph)
    for m in err2:
        issues.append({"level":"error","code":"STEP_MULTIPLE_OUTGOING","message": m})

    ok3, err3 = _edges_ok(graph)
    for m in err3:
        issues.append({"level":"error","code":"EDGE_INVALID","message": m})

    preflight_block: Dict[str, Any] = {}
    if include_preflight:
        st = _resolve_strict_tools(graph, strict_tools)
        errors_pf, warnings_pf = run_all_checks(graph, strict_tools=st)
        preflight_block = {"errors": errors_pf, "warnings": warnings_pf, "strict_tools": st}
        # merge into issues with neutral codes (non-breaking)
        for w in warnings_pf:
            issues.append({"level":"warning","code":"PREFLIGHT","message": w})
        for e in errors_pf:
            issues.append({"level":"error","code":"PREFLIGHT","message": e})
        # Persist side effects if requested
        if persist:
            try:
                from .runner_parts.preflight_checks import preflight_extra_checks
                ok = preflight_extra_checks(graph, dbp, worker_name, strict_tools=st)
                if not ok:
                    # preflight_extra_checks already persisted details and phase
                    pass
            except Exception:
                pass

    accepted = not any(it.get("level") == "error" for it in issues)
    nodes_total = int(counts.get("total_steps", 0)) + int(counts.get("total_conds", 0)) + int((counts.get("types") or {}).get("symbolic", 0))
    nodes_breakdown = dict(counts.get("types", {}))

    out: Dict[str, Any] = {
        "accepted": accepted,
        "status": ("ok" if accepted else "error"),
        "issues": issues,
        "summary": counts,
        "nodes_total": nodes_total,
        "nodes_breakdown": nodes_breakdown,
        "limit_steps": limit_steps,
        "truncated": False,
        "graph": graph,
    }
    if include_preflight:
        out["preflight"] = preflight_block
    return out
