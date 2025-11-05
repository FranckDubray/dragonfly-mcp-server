from __future__ import annotations
from typing import Dict, Any

async def get_config(worker_name: str) -> Dict[str, Any]:
    from src.tools._py_orchestrator.api_router import route as py_route
    return py_route({
        "operation": "config",
        "worker_name": worker_name,
    })
