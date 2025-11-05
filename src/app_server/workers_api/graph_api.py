from __future__ import annotations
from typing import Dict, Any, Optional

# Renvoie soit Mermaid, soit JSON nodes/edges, selon param mermaid

async def get_graph(
    worker_name: str,
    kind: str = "process",
    subgraph: Optional[str] = None,
    mermaid: bool = True,
    overview: bool = False,
    hide_start: bool = False,
    hide_end: bool = False,
    labels: bool = True,
) -> Dict[str, Any]:
    from src.tools._py_orchestrator.api_router import route as py_route

    graph_req: Dict[str, Any] = {
        "kind": kind,
        "include": {"shapes": True, "emojis": True, "labels": labels},
        "render": {"mermaid": mermaid, "hide_start": hide_start, "hide_end": hide_end, "overview_subgraphs": overview},
    }
    if kind == "subgraph" and subgraph:
        graph_req["subgraphs"] = [subgraph]

    return py_route({
        "operation": "graph",
        "worker_name": worker_name,
        "graph": graph_req,
    })
