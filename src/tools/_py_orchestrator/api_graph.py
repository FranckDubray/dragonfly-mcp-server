




from pathlib import Path
import json
from typing import Dict, Any, List

from .validators import validate_params, PY_WORKERS_DIR, validate_worker_name
from .controller_parts.graph_build import validate_and_extract_graph
from .api_spawn import db_path_for_worker
from .db import get_state_kv

# Emoji mapping for canonical categories
CATEGORY_EMOJI = {
    "intelligence": "\U0001F4CA",   # 📊
    "development": "\U0001F527",    # 🔧
    "communication": "\u2709\ufe0f",# ✉️
    "data": "\U0001F5C4\ufe0f",    # 🗄️
    "documents": "\U0001F4C4",      # 📄
    "media": "\U0001F3AC",          # 🎬
    "transportation": "\u2708\ufe0f",# ✈️
    "networking": "\U0001F310",     # 🌐
    "utilities": "\U0001F522",       # 🔢
    "entertainment": "\U0001F3AE",   # 🎮
}

SPEC_ROOT = Path(__file__).resolve().parents[2] / "tool_specs"


def _tool_category(tool_name: str) -> str:
    try:
        spec_path = SPEC_ROOT / f"{tool_name}.json"
        if not spec_path.is_file():
            return ""
        obj = json.loads(spec_path.read_text(encoding="utf-8"))
        cat = (((obj or {}).get("function") or {}).get("category"))
        return str(cat or "")
    except Exception:
        return ""


def _shape_for(node: Dict[str, Any]) -> Dict[str, Any]:
    t = node.get("type")
    call_kind = node.get("call_kind")
    call_target = node.get("call_target")
    if t == "cond":
        return {"shape": "diamond", "color": "default", "emoji": ""}
    if t == "step":
        if call_kind == "transform":
            # Always gear emoji for transforms
            return {"shape": "rect", "color": "blue", "emoji": "\u2699\ufe0f"}
        if call_kind == "tool":
            # Tool emoji based on canonical category
            cat = _tool_category(str(call_target or ""))
            em = CATEGORY_EMOJI.get(cat, "\U0001FAE9")
            return {"shape": "rect", "color": "green", "emoji": em, "category": cat}
    return {"shape": "rect", "color": "default", "emoji": ""}


def _build_mermaid_plain(graph: Dict[str, Any], include: Dict[str, Any]) -> str:
    """Build a plain Mermaid (no server-side styling). Ensure IDs are fully-qualified SG::STEP and
    conditionals are diamonds with labeled outgoing edges."""
    nodes = graph.get('nodes', [])
    edges = graph.get('edges', [])
    subgraphs = graph.get('subgraphs', {})

    # Helper to qualify node IDs consistently
    entry_by_sg = {sg: (info or {}).get('entry') for sg, info in subgraphs.items()}

    def qual(node_id: str, default_sg: str | None = None) -> str:
        if not node_id:
            return node_id
        if node_id in {"START", "END"}:
            return node_id
        if "::" in node_id:
            return node_id
        if default_sg:
            return f"{default_sg}::{node_id}"
        for sg, entry in entry_by_sg.items():
            if entry == node_id:
                return f"{sg}::{node_id}"
        return node_id

    lines: List[str] = ["graph TD"]

    # START at top if any
    has_start = any(n.get('type') == 'start' for n in nodes)
    if has_start:
        lines.append("  START")

    # Group nodes by subgraph
    by_sg: Dict[str, List[Dict[str, Any]]] = {}
    for n in nodes:
        sg = n.get('subgraph') or '__ROOT__'
        by_sg.setdefault(sg, []).append(n)

    # Subgraph clusters with fully-qualified node IDs and correct shapes
    for sg_name, info in subgraphs.items():
        label = sg_name
        lines.append(f"  subgraph {label}")
        for n in by_sg.get(sg_name, []):
            node_type = n.get('type')
            node_id = f"{sg_name}::{n['name']}" if node_type not in {'start', 'end'} else n['name']
            lab = n['name']
            if include.get('emojis', True):
                shape = _shape_for(n)
                em = shape.get('emoji') or ''
                if em:
                    lab = f"{em} {lab}"
            # Diamond for conds
            if node_type == 'cond':
                lines.append(f"    {node_id}{{{lab}}}")
            else:
                lines.append(f"    {node_id}[{lab}]")
        lines.append("  end")

    # Nodes not in subgraphs: only END (avoid duplicate START)
    for n in by_sg.get('__ROOT__', []):
        if n.get('type') == 'end':
            lines.append(f"  {n['name']}")

    # Edges with qualification + labels for when != 'always'
    add_labels = include.get('labels', True)
    for e in edges:
        src_raw = e.get('from')
        dst_raw = e.get('to')
        when = e.get('when')
        default_sg = e.get('subgraph')
        src = qual(str(src_raw), default_sg)
        dst = qual(str(dst_raw), default_sg)
        if add_labels and when and when != 'always':
            lines.append(f"  {src}-->|{when}|{dst}")
        else:
            lines.append(f"  {src}-->{dst}")

    # Style symbolic nodes START/END in green
    if has_start:
        lines.append("  style START fill:#d9fdd3,stroke:#2e7d32,stroke-width:1px")
    # Check if END exists among nodes
    has_end = any(n.get('type') == 'end' for n in nodes) or any(n.get('name') == 'END' for n in nodes)
    if has_end:
        lines.append("  style END fill:#d9fdd3,stroke:#2e7d32,stroke-width:1px")

    return "\n".join(lines)


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

    nodes = g.get("nodes", [])
    edges = g.get("edges", [])
    subgraphs = g.get("subgraphs", {})

    # Filter for requested kind
    if kind == "subgraph":
        wanted = set([str(s) for s in subgraphs_req if s in subgraphs])
        if not wanted:
            return {"accepted": False, "status": "error", "message": "No valid subgraph specified"}
        keep_sg = set(wanted)
        nodes = [n for n in nodes if n.get("subgraph") in keep_sg or n.get("type") in {"start","end"}]
        edges = [e for e in edges if (e.get("subgraph") in keep_sg) or ("::" in str(e.get("from","")) and str(e.get("from")).split("::")[0] in keep_sg)]

    elif kind == "current_subgraph":
        # Derive current position from KV
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
        cur, nxt = _current_position()
        cur_sg = cur.split("::", 1)[0] if "::" in cur else (nxt.split("::", 1)[0] if "::" in nxt else "")
        if not cur_sg or cur_sg not in subgraphs:
            return {"accepted": False, "status": "error", "message": "Cannot determine current subgraph"}
        nodes = [n for n in nodes if n.get("subgraph") == cur_sg or n.get("type") in {"start","end"}]
        edges = [e for e in edges if (e.get("subgraph") == cur_sg) or ("::" in str(e.get("from","")) and str(e.get("from")).split("::"))[0] == cur_sg]

    # Render Mermaid only when requested
    if (render or {}).get("mermaid") is True:
        try:
            mm = _build_mermaid_plain({"nodes": nodes, "edges": edges, "subgraphs": subgraphs}, include=include)
            return {"accepted": True, "status": "ok", "mermaid": mm, "truncated": False}
        except Exception as e:
            return {"accepted": False, "status": "error", "message": f"Mermaid build failed: {str(e)[:200]}"}

    # Otherwise, return nodes/edges (legacy)
    out_nodes: List[Dict[str, Any]] = []
    for n in nodes:
        if n.get("type") in {"start","end"}:
            out_nodes.append({"id": n.get("name"), "label": n.get("name"), "type": n.get("type")})
            continue
        shape = _shape_for(n)
        item = {
            "id": f"{n.get('subgraph')}::{n.get('name')}",
            "label": n.get("name"),
            "type": n.get("type"),
            "subgraph": n.get("subgraph"),
        }
        if include.get("shapes", True):
            item.update({"shape": shape.get("shape"), "color": shape.get("color")})
        if include.get("emojis", True):
            if shape.get("emoji"):
                item["emoji"] = shape.get("emoji")
            if shape.get("category"):
                item["category"] = shape.get("category")
        out_nodes.append(item)

    out_edges: List[Dict[str, Any]] = []
    add_labels = include.get("labels", True)
    for e in edges:
        src = e.get("from")
        dst = e.get("to")
        when = e.get("when")
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
