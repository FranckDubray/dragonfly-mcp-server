






















from pathlib import Path
import json
import re
from typing import Dict, Any, List

CATEGORY_EMOJI = {
    "intelligence": "\U0001F4CA",
    "development": "\U0001F527",
    "communication": "\u2709\ufe0f",
    "data": "\U0001F5C4\ufe0f",
    "documents": "\U0001F4C4",
    "media": "\U0001F3AC",
    "transportation": "\u2708\ufe0f",
    "networking": "\U0001F310",
    "utilities": "\U0001F522",
    "entertainment": "\U0001F3AE",
}

COLOR_TOOL_FILL = "#E9D5FF"
COLOR_TOOL_STROKE = "#7C3AED"
COLOR_TRANS_FILL = "#D0E7FF"
COLOR_TRANS_STROKE = "#1565C0"
COLOR_TERM_FILL = "#d9fdd3"
COLOR_TERM_STROKE = "#2e7d32"
COLOR_COND_FILL = "#FFE0B2"
COLOR_COND_STROKE = "#EF6C00"

# Highlights for overview
COLOR_OV_CURRENT_FILL = "#C7EBFF"   # light blue highlight
COLOR_OV_CURRENT_STROKE = "#0B74C4"  # stronger blue stroke
COLOR_OV_ENTRY_STROKE = "#10b981"    # green stroke for entry

SPEC_ROOT = Path(__file__).resolve().parents[2] / "tool_specs"

_valid_id_re = re.compile(r"[^A-Za-z0-9_]")

def _safe_id(s: str) -> str:
    return _valid_id_re.sub("_", str(s or "")).strip("_") or "N"


def _tool_category(tool_name: str) -> str:
    try:
        spec_path = SPEC_ROOT / f"{tool_name}.json"
        if not spec_path.is_file():
            return ""
        obj = json.loads(spec_path.read_text(encoding="utf-8"))
        return str((((obj or {}).get("function") or {}).get("category")) or "")
    except Exception:
        return ""


def _shape_for(node: Dict[str, Any], include: Dict[str, Any]) -> str:
    t = node.get("type")
    call_kind = node.get("call_kind")
    call_target = node.get("call_target")
    label = node.get('name', '')
    em = ''
    if t == "cond":
        return f"{{{label}}}", f"fill:{COLOR_COND_FILL},stroke:{COLOR_COND_STROKE},stroke-width:1px"
    if t == "step":
        if call_kind == "transform":
            if include.get('emojis', True):
                em = "\u2699\ufe0f "
            return f"[{em}{label}]", f"fill:{COLOR_TRANS_FILL},stroke:{COLOR_TRANS_STROKE},stroke-width:1px"
        if call_kind == "tool":
            cat = _tool_category(str(call_target or ""))
            if include.get('emojis', True):
                em = CATEGORY_EMOJI.get(cat, "\U0001F4AC") + " "
            return f"[{em}{label}]", f"fill:{COLOR_TOOL_FILL},stroke:{COLOR_TOOL_STROKE},stroke-width:1px"
    return f"[{label}]", ""


def build_mermaid_plain(graph: Dict[str, Any], include: Dict[str, Any], render: Dict[str, Any] | None = None) -> str:
    render = render or {}
    hide_start = bool(render.get("hide_start"))
    hide_end = bool(render.get("hide_end"))
    flat = bool(render.get("no_clusters"))

    nodes = graph.get('nodes', [])
    edges = graph.get('edges', [])
    subgraphs = graph.get('subgraphs', {})

    entry_by_sg = {sg: (info or {}).get('entry') for sg, info in subgraphs.items()}

    def qual(node_id: str, default_sg: str | None = None) -> str:
        if not node_id or node_id in {"START", "END"} or "::" in node_id:
            return node_id
        if default_sg:
            return f"{default_sg}::{node_id}"
        for sg, entry in entry_by_sg.items():
            if entry == node_id:
                return f"{sg}::{node_id}"
        return node_id

    lines: List[str] = ["graph TD"]
    style_lines: List[str] = []

    has_start = any(n.get('type') == 'start' for n in nodes)
    if has_start and not hide_start:
        # Retirer les emojis pour éviter des nœuds START/END surdimensionnés
        lines.append("  START((START))")

    by_sg: Dict[str, List[Dict[str, Any]]] = {}
    for n in nodes:
        sg = n.get('subgraph') or '__ROOT__'
        by_sg.setdefault(sg, []).append(n)

    # Nodes drawing
    id_map: Dict[str, str] = {}
    if flat:
        # Draw all nodes (except START/END) at root level
        for n in nodes:
            if n.get('type') in {'start','end'}:
                continue
            sg = n.get('subgraph') or ''
            raw_id = f"{sg}::{n['name']}" if sg else n['name']
            node_id = _safe_id(raw_id)
            id_map[raw_id] = node_id
            node_label, style = _shape_for(n, include)
            lines.append(f"  {node_id}{node_label}")
            if style:
                style_lines.append(f"  style {node_id} {style}")
    else:
        # Subgraph clusters
        for sg_name, info in subgraphs.items():
            lines.append(f"  subgraph {sg_name}")
            for n in by_sg.get(sg_name, []):
                node_type = n.get('type')
                if node_type in {'start','end'}:
                    continue
                raw_id = f"{sg_name}::{n['name']}"
                node_id = _safe_id(raw_id)
                id_map[raw_id] = node_id
                node_label, style = _shape_for(n, include)
                lines.append(f"    {node_id}{node_label}")
                if style:
                    style_lines.append(f"  style {node_id} {style}")
            lines.append("  end")

    if not hide_end:
        for n in by_sg.get('__ROOT__', []):
            if n.get('type') == 'end':
                lines.append("  END((END))")

    add_labels = include.get('labels', True)
    seen = set()
    EXIT_MARKS = {"success","fail","retry","retry_exhausted"}
    for e in edges:
        src_raw = str(e.get('from'))
        dst_raw = str(e.get('to'))
        when = e.get('when')
        default_sg = e.get('subgraph')
        # Skip edges that point to or originate from pseudo-exit nodes (SG::success, etc.)
        if '::' in dst_raw and dst_raw.split('::',1)[1] in EXIT_MARKS:
            continue
        if '::' in src_raw and src_raw.split('::',1)[1] in EXIT_MARKS:
            continue
        if hide_start and src_raw == 'START':
            continue
        if hide_end and dst_raw == 'END':
            continue
        src_q = qual(src_raw, default_sg)
        dst_q = qual(dst_raw, default_sg)
        src = id_map.get(src_q, _safe_id(src_q))
        dst = id_map.get(dst_q, _safe_id(dst_q))
        key = (src, dst, when or '')
        if key in seen:
            continue
        seen.add(key)
        if add_labels and when and when != 'always':
            lines.append(f"  {src}--> |{when}| {dst}")
        else:
            lines.append(f"  {src}--> {dst}")

    if has_start and not hide_start:
        style_lines.append(f"  style START fill:{COLOR_TERM_FILL},stroke:{COLOR_TERM_STROKE},stroke-width:1px")
    has_end = any(n.get('type') == 'end' for n in nodes) or any(n.get('name') == 'END' for n in nodes)
    if has_end and not hide_end:
        style_lines.append(f"  style END fill:{COLOR_TERM_FILL},stroke:{COLOR_TERM_STROKE},stroke-width:1px")

    return "\n".join(lines + style_lines)


def build_mermaid_overview(graph: Dict[str, Any], render: Dict[str, Any] | None = None) -> str:
    render = render or {}
    hide_start = bool(render.get("hide_start"))
    hide_end = bool(render.get("hide_end"))

    subgraphs = graph.get('subgraphs', {})
    order = graph.get('order', [])

    lines: List[str] = ["graph TD"]
    style_lines: List[str] = []

    if not hide_start:
        lines.append("  START((START))")

    # Nodes (each subgraph as a single node)
    for sg in order:
        lines.append(f"  {_safe_id(sg)}([{sg}])")

    entry = graph.get('entry')
    if entry and not hide_start:
        lines.append(f"  START--> {_safe_id(entry)}")

    next_map = {sg: (subgraphs.get(sg, {}) or {}).get('next', {}) or {} for sg in order}
    seen = set()
    for sg in order:
        sg_id = _safe_id(sg)
        for exit_label, target in (next_map.get(sg) or {}).items():
            if target and target in order:
                tgt_id = _safe_id(target)
                key = (f"{sg}::{exit_label}", target)
                if key in seen:
                    continue
                seen.add(key)
                lines.append(f"  {sg_id}--> |{exit_label}| {tgt_id}")
    for i, sg in enumerate(order[:-1]):
        if 'success' not in (next_map.get(sg) or {}):
            nxt = order[i+1]
            lines.append(f"  {_safe_id(sg)}--> |success| {_safe_id(nxt)}")

    if order and not hide_end:
        last = order[-1]
        has_success_out = 'success' in (next_map.get(last) or {})
        if not has_success_out:
            lines.append("  END((END))")
            lines.append(f"  {_safe_id(last)}--> |success| END")

    # Highlight current and entry if provided
    try:
      hl = (render or {}).get('highlight') or {}
      cur = (hl or {}).get('current_subgraph') or ''
      ent = (hl or {}).get('entry') or ''
      if isinstance(cur, str) and cur.strip():
          style_lines.append(f"  style {_safe_id(cur.strip())} fill:{COLOR_OV_CURRENT_FILL},stroke:{COLOR_OV_CURRENT_STROKE},stroke-width:2px")
      if isinstance(ent, str) and ent.strip():
          style_lines.append(f"  style {_safe_id(ent.strip())} stroke:{COLOR_OV_ENTRY_STROKE},stroke-width:2px,stroke-dasharray: 3 2")
    except Exception:
      pass

    return "\n".join(lines + style_lines)

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 

 
