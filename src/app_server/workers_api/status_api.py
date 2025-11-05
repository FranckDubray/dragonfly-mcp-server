from __future__ import annotations
from typing import Dict, Any

async def get_status(worker_name: str) -> Dict[str, Any]:
    from src.tools._py_orchestrator.api_router import route as py_route
    # include_metrics True par défaut pour UI
    return py_route({
        "operation": "status",
        "worker_name": worker_name,
        "include_metrics": True,
    })
