
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
        nodes = [n for n in nodes if n.get("subgraph") in keep_sg or n.get("type") in {"start","end"}]
        edges = [e for e in edges if (e.get("subgraph") in keep_sg) or ("::" in str(e.get("from","")) and str(e.get("from","")) .split("::",1)[0] == list(keep_sg)[0])]
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
