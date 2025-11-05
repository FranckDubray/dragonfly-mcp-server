from __future__ import annotations
from typing import Dict, Any, Optional

async def debug_action(
    worker_name: str,
    action: str,
    timeout_sec: Optional[float] = None,
    target_node: Optional[str] = None,
    target_when: Optional[str] = None,
    break_node: Optional[str] = None,
    break_when: Optional[str] = None,
) -> Dict[str, Any]:
    from src.tools._py_orchestrator.api_router import route as py_route
    dbg: Dict[str, Any] = {"action": action}
    if timeout_sec is not None:
        dbg["timeout_sec"] = float(timeout_sec)
    if target_node or target_when:
        dbg["target"] = {"node": target_node, "when": target_when}
    if break_node or break_when:
        dbg["breakpoint"] = {"node": break_node, "when": break_when}
    return py_route({
        "operation": "debug",
        "worker_name": worker_name,
        "debug": dbg,
    })
