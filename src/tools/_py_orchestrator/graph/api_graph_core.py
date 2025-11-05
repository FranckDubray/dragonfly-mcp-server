
from typing import Dict, Any, List
from .mermaid_builders import build_mermaid_plain, build_mermaid_overview


def filter_graph(g: Dict[str, Any], kind: str, subgraphs_req: List[str]) -> Dict[str, Any]:
    nodes = g.get("nodes", [])
    edges = g.get("edges", [])
    subgraphs = g.get("subgraphs", {})

    if kind == "subgraph":
        wanted = set([str(s) for s in subgraphs_req if s in subgraphs])
        if not wanted:
            return {"error": "No valid subgraph specified"}
        keep_sg = set(wanted)
        # Keep only nodes in requested subgraphs (plus START/END if ever present at root)
        nodes = [n for n in nodes if n.get("subgraph") in keep_sg or n.get("type") in {"start","end"}]
        # Keep only edges within requested subgraphs or edges whose 'from' pseudo-exit originates from one of them
        def _edge_in_scope(e: Dict[str, Any]) -> bool:
            if e.get("subgraph") in keep_sg:
                return True
            src = str(e.get("from", ""))
            if "::" in src and src.split("::", 1)[0] in keep_sg:
                return True
            return False
        edges = [e for e in edges if _edge_in_scope(e)]
        # Prune subgraphs map to the requested ones
        subgraphs = {k: v for k, v in (subgraphs or {}).items() if k in keep_sg}
    return {"nodes": nodes, "edges": edges, "subgraphs": subgraphs}


def graph_to_mermaid(g: Dict[str, Any], include: Dict[str, Any], render: Dict[str, Any]) -> Dict[str, Any]:
    try:
        mm = build_mermaid_plain({"nodes": g.get("nodes"), "edges": g.get("edges"), "subgraphs": g.get("subgraphs")}, include=include, render=render)
        return {"accepted": True, "status": "ok", "mermaid": mm, "truncated": False}
    except Exception as e:
        return {"accepted": False, "status": "error", "message": f"Mermaid build failed: {str(e)[:200]}"}


def overview_to_mermaid(g: Dict[str, Any], render: Dict[str, Any]) -> Dict[str, Any]:
    try:
        mm = build_mermaid_overview(g, render=render)
        return {"accepted": True, "status": "ok", "mermaid": mm, "truncated": False}
    except Exception as e:
        return {"accepted": False, "status": "error", "message": f"Mermaid overview build failed: {str(e)[:200]}"}
