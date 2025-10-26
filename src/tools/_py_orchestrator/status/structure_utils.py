
from typing import Any, Dict, List
from ..validators import PY_WORKERS_DIR
from ..controller_parts.graph_build import validate_and_extract_graph


def structure_counts(worker_name: str) -> Dict[str, Any]:
    try:
        root = PY_WORKERS_DIR / worker_name
        if not root.exists():
            return {}
        g = validate_and_extract_graph(root)
        nodes = g.get("nodes", [])
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
        nodes_total = total_steps + total_conds + types["symbolic"]
        return {
            "nodes_total": nodes_total,
            "nodes_breakdown": types,
            "per_subgraph": per_sg,
            "total_steps": total_steps,
            "total_conds": total_conds,
        }
    except Exception:
        return {}


def split_node(full: str) -> Dict[str, str]:
    try:
        if '::' in full:
            sg, step = full.split('::', 1)
            return {"subgraph": sg, "step": step, "full": full}
        return {"subgraph": "", "step": full or "", "full": full or ""}
    except Exception:
        return {"subgraph": "", "step": full or "", "full": full or ""}


def topo_order_for_subgraph(worker_name: str, sg: str, graph: Dict[str, Any] | None = None) -> List[str]:
    try:
        if graph is None:
            root = PY_WORKERS_DIR / worker_name
            graph = validate_and_extract_graph(root)
        nodes = [n for n in (graph.get('nodes') or []) if n.get('subgraph') == sg and n.get('type') in {'step', 'cond'}]
        names = sorted([n.get('name') for n in nodes if n.get('name')])
        name_set = set(names)
        edges = [e for e in (graph.get('edges') or []) if e.get('subgraph') == sg]
        adj: Dict[str, List[str]] = {n: [] for n in names}
        indeg: Dict[str, int] = {n: 0 for n in names}
        for e in edges:
            src = e.get('from')
            dst = e.get('to')
            if src in name_set and dst in name_set:
                adj[src].append(dst)
                indeg[dst] += 1
        zero = sorted([n for n, d in indeg.items() if d == 0])
        out: List[str] = []
        from bisect import insort
        while zero:
            u = zero.pop(0)
            out.append(u)
            for v in sorted(adj.get(u, [])):
                indeg[v] -= 1
                if indeg[v] == 0:
                    insort(zero, v)
        if len(out) != len(names):
            return names
        return out
    except Exception:
        return []


def progress_for_node(worker_name: str, full: str) -> Dict[str, Any]:
    try:
        if not full:
            return {}
        parts = split_node(full)
        sg = parts.get('subgraph') or ''
        step = parts.get('step') or ''
        if not sg or not step:
            return {}
        root = PY_WORKERS_DIR / worker_name
        g = validate_and_extract_graph(root)
        order = topo_order_for_subgraph(worker_name, sg, graph=g)
        total = len(order)
        try:
            index = order.index(step)
        except ValueError:
            index = -1
        entry = ((g.get('subgraphs') or {}).get(sg) or {}).get('entry') or ''
        return {"subgraph": sg, "index": index, "total": total, "entry": entry, "current_step": step, "order": order}
    except Exception:
        return {}
