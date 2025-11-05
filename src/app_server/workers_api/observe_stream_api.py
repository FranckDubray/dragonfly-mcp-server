from __future__ import annotations
from typing import AsyncGenerator, Dict, Any
import asyncio
import json

# NDJSON streaming wrapper over py_orchestrator observe (passive)
# Maintains a from_rowid cursor to avoid duplicates, emits terminal event and last_rowid hints.

TERMINALS = {"completed", "failed", "canceled", "terminal"}

async def _gen_stream(worker_name: str, timeout_sec: float = 10.0, max_events: int = 50) -> AsyncGenerator[bytes, None]:
    from src.tools._py_orchestrator.api_router import route as py_route
    last_rowid = 0
    while True:
        # Ask py_orchestrator for a short window of events, resuming from last_rowid
        req: Dict[str, Any] = {
            "operation": "observe",
            "worker_name": worker_name,
            "observe": {"timeout_sec": timeout_sec, "max_events": max_events}
        }
        if last_rowid > 0:
            req["observe"]["from_rowid"] = last_rowid
        res: Dict[str, Any] = py_route(req)
        if isinstance(res, dict):
            # Update cursor if provided
            try:
                lr = int(res.get("last_rowid") or 0)
                if lr > 0:
                    last_rowid = lr
            except Exception:
                pass

            evs = list(res.get("events") or [])
            for ev in evs:
                # annotate with last_rowid for clients that want to track
                try:
                    if last_rowid and isinstance(ev, dict):
                        ev.setdefault("last_rowid", last_rowid)
                except Exception:
                    pass
                try:
                    line = (json.dumps(ev, ensure_ascii=False) + "\n").encode("utf-8")
                except Exception:
                    line = (str(ev).replace("\n", " ") + "\n").encode("utf-8", errors="ignore")
                yield line

            status = str(res.get("status") or "").lower()
            if status in TERMINALS:
                # Emit a terminal chunk then stop
                term = {"chunk_type": "terminal", "phase": status, "last_rowid": last_rowid}
                try:
                    yield (json.dumps(term, ensure_ascii=False) + "\n").encode("utf-8")
                except Exception:
                    pass
                return
        # Small backoff to avoid hot loop when no events
        await asyncio.sleep(0.2)

async def stream_ndjson(worker_name: str, timeout_sec: float = 10.0, max_events: int = 50):
    from fastapi.responses import StreamingResponse
    # Use NDJSON but force no buffering in proxies; keep semantics simple for fetch streaming.
    return StreamingResponse(
        _gen_stream(worker_name, timeout_sec, max_events),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
