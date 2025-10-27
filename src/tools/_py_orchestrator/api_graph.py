
from pathlib import Path
from typing import Dict, Any, List

from .validators import validate_params, PY_WORKERS_DIR, validate_worker_name
from .controller_parts.graph_build import validate_and_extract_graph
from .api_spawn import db_path_for_worker
from .db import get_state_kv

# thin wrappers moved to graph/ to keep this module small (<7KB)
from .graph.api_graph_core import filter_graph, graph_to_mermaid, overview_to_mermaid


def graph(params: dict) -> dict:
    p = validate_params({**params, "operation": "graph"})
    worker_name = validate_worker_name(p.get("worker_name"))
    worker_root = (PY_WORKERS_DIR / worker_name)
    if not worker_root.exists():
        return {"accepted": False, "status": "error", "message": f"Worker root not found: {worker_name}"}

    try:
        g = validate_and_extract_graph(worker_root)
    except Exception as e:
        return {"accepted": False, "status": "error", "message": f"Graph extraction failed: {str(e)[:350]}"}

    graph_req = (params or {}).get("graph") or {}
    kind = str(graph_req.get("kind") or "process")
    subgraphs_req = graph_req.get("subgraphs") or []
    include = graph_req.get("include") or {"shapes": True, "emojis": True, "labels": True}
    render = (graph_req.get("render") or {}) if isinstance(graph_req.get("render"), dict) else {}

    # Filter kinds
    if kind == "subgraph":
        fg = filter_graph(g, kind, subgraphs_req)
        if "error" in fg:
            return {"accepted": False, "status": "error", "message": fg["error"]}
        nodes = fg["nodes"]; edges = fg["edges"]; subgraphs = fg["subgraphs"]
    elif kind == "current_subgraph":
        def _current_position():
            try:
                db_path = db_path_for_worker(worker_name)
                cur = get_state_kv(db_path, worker_name, 'debug.paused_at') or ''
                if not cur:
                    cur = get_state_kv(db_path, worker_name, 'debug.executing_node') or ''
                nxt = get_state_kv(db_path, worker_name, 'debug.next_node') or ''
                return cur, nxt
            except Exception:
                return '', ''
        nodes = g.get("nodes", []); edges = g.get("edges", []); subgraphs = g.get("subgraphs", {})
        cur, nxt = _current_position()
        cur_sg = cur.split("::", 1)[0] if "::" in cur else (nxt.split("::", 1)[0] if "::" in nxt else "")
        if not cur_sg or cur_sg not in subgraphs:
            return {"accepted": False, "status": "error", "message": "Cannot determine current subgraph"}
        nodes = [n for n in nodes if n.get("subgraph") == cur_sg or n.get("type") in {"start","end"}]
        edges = [e for e in edges if (e.get("subgraph") == cur_sg) or ("::" in str(e.get("from","")) and str(e.get("from","")) .split("::",1)[0] == cur_sg)]
    else:
        nodes = g.get("nodes", []); edges = g.get("edges", []); subgraphs = g.get("subgraphs", {})

    if (render or {}).get("overview_subgraphs") is True:
        return overview_to_mermaid(g, render)

    if (render or {}).get("mermaid") is True:
        return graph_to_mermaid({"nodes": nodes, "edges": edges, "subgraphs": subgraphs}, include, render)

    # Legacy JSON (nodes/edges) unchanged
    out_nodes: List[Dict[str, Any]] = []
    for n in nodes:
        if n.get("type") in {"start","end"}:
            out_nodes.append({"id": n.get("name"), "label": n.get("name"), "type": n.get("type")})
            continue
        # Keep minimal shape hints so UI can colorize
        item = {
            "id": f"{n.get('subgraph')}::{n.get('name')}",
            "label": n.get("name"),
            "type": n.get("type"),
            "subgraph": n.get("subgraph"),
            "call_kind": n.get("call_kind"),
            "call_target": n.get("call_target"),
        }
        out_nodes.append(item)

    out_edges: List[Dict[str, Any]] = []
    add_labels = include.get("labels", True)
    for e in edges:
        src = e.get("from"); dst = e.get("to"); when = e.get("when")
        if isinstance(dst, str) and '::' in dst and dst.split('::',1)[1] in {"success","fail","retry","retry_exhausted"}:
            continue
        rec = {"from": src, "to": dst}
        if add_labels and when and when != "always":
            rec["label"] = when
        out_edges.append(rec)

    return {
        "accepted": True,
        "status": "ok",
        "kind": kind,
        "nodes": out_nodes,
        "edges": out_edges,
        "truncated": False,
    }
