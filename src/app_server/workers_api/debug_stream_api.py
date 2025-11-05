from __future__ import annotations
from typing import AsyncGenerator, Dict, Any
import asyncio
import json
from fastapi.responses import StreamingResponse

# NDJSON streaming wrapper over py_orchestrator debug action=stream

async def _gen_stream(worker_name: str, timeout_sec: float = 10.0, max_events: int = 50) -> AsyncGenerator[bytes, None]:
    from src.tools._py_orchestrator.api_router import route as py_route
    # loop until terminal status
    while True:
        res: Dict[str, Any] = py_route({
            "operation": "debug",
            "worker_name": worker_name,
            "debug": {"action": "stream", "timeout_sec": timeout_sec, "max_events": max_events},
        })
        evs = list(res.get("events") or []) if isinstance(res, dict) else []
        for ev in evs:
            try:
                line = (json.dumps(ev, ensure_ascii=False) + "\n").encode("utf-8")
            except Exception:
                line = (str(ev).replace("\n", " ") + "\n").encode("utf-8", errors="ignore")
            yield line
        status = str(res.get("status") or "").lower() if isinstance(res, dict) else ""
        if status in {"completed", "failed", "canceled", "terminal"}:
            return
        # Small pause to avoid tight loop if no events
        await asyncio.sleep(0.15)

async def stream_ndjson(worker_name: str, timeout_sec: float = 10.0, max_events: int = 50) -> StreamingResponse:
    return StreamingResponse(_gen_stream(worker_name, timeout_sec, max_events), media_type="application/x-ndjson")
