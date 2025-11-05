



















from __future__ import annotations
from typing import AsyncGenerator, Dict, Any, List
import asyncio
import json
import sqlite3
from pathlib import Path

# NDJSON streaming: emits compact updates for multiple workers (phase/heartbeat/last_step_at)
# Now also hints when a worker is currently running a tool call (best-effort):
#  - running_kind: 'tool' | 'other' | ''
#  - running_started_at: ISO timestamp if available
# And minimal step info for live process view without per-worker SSE:
#  - last_node: last executed node name
#  - last_io_call: minimal call object
#  - last_io_out_preview: preview string

async def _gen_stream(timeout_sec: float = 0.0, max_events: int = 0) -> AsyncGenerator[bytes, None]:
    from src.tools._py_orchestrator.api_common import SQLITE_DIR

    base = Path(SQLITE_DIR)
    sent = 0
    start = asyncio.get_event_loop().time()
    last_snap: Dict[str, Dict[str, Any]] = {}

    async def _sleep(t: float):
        try:
            await asyncio.sleep(t)
        except Exception:
            pass

    def _list_workers() -> List[Path]:
        return sorted(p for p in base.glob("worker_*.db") if p.is_file())

    def _read_state(dbp: Path, worker_name: str) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        try:
            conn = sqlite3.connect(str(dbp), timeout=1.5)
            try:
                # Phase / heartbeat / last step timestamp (finished or started)
                cur = conn.execute("SELECT svalue FROM job_state_kv WHERE worker=? AND skey=?", (worker_name, 'phase'))
                row = cur.fetchone(); out['phase'] = (row[0] if row and row[0] is not None else '')
                cur = conn.execute("SELECT svalue FROM job_state_kv WHERE worker=? AND skey=?", (worker_name, 'heartbeat'))
                row = cur.fetchone(); out['heartbeat'] = (row[0] if row and row[0] is not None else '')
                cur = conn.execute("SELECT COALESCE(finished_at, started_at) FROM job_steps WHERE worker=? ORDER BY rowid DESC LIMIT 1", (worker_name,))
                row = cur.fetchone(); out['last_step_at'] = (row[0] if row and row[0] is not None else '')

                # Minimal info for current/last step
                out['last_node'] = ''
                out['last_io_call'] = {}
                out['last_io_out_preview'] = ''
                try:
                    cur = conn.execute(
                        "SELECT node, status, details_json, started_at, finished_at FROM job_steps WHERE worker=? ORDER BY rowid DESC LIMIT 1",
                        (worker_name,)
                    )
                    r3 = cur.fetchone()
                    if r3:
                        node, st, dj, st_at, fin = r3
                        if node: out['last_node'] = str(node)
                        if dj:
                            try:
                                obj = json.loads(dj)
                                call = obj.get('call') if isinstance(obj, dict) else None
                                if isinstance(call, dict):
                                    out['last_io_call'] = call
                                lrp = obj.get('last_result_preview') if isinstance(obj, dict) else None
                                if lrp is not None:
                                    out['last_io_out_preview'] = lrp if isinstance(lrp, str) else str(lrp)
                            except Exception:
                                pass
                except Exception:
                    pass

                # Best-effort: detect current running step kind (tool vs other)
                out['running_kind'] = ''
                out['running_started_at'] = ''
                try:
                    cur = conn.execute(
                        "SELECT status, details_json, started_at FROM job_steps WHERE worker=? ORDER BY rowid DESC LIMIT 1",
                        (worker_name,)
                    )
                    r2 = cur.fetchone()
                    if r2:
                        st, dj, st_at = r2
                        st_l = str(st or '').lower()
                        if st_l in {'running', 'executing', 'in_progress'}:
                            # Default to 'other', refine with details_json.call
                            rkind = 'other'
                            if dj:
                                try:
                                    obj = json.loads(dj)
                                    call = obj.get('call') if isinstance(obj, dict) else None
                                    if isinstance(call, dict):
                                        if 'tool' in call or 'tool_name' in call or 'operation' in call:
                                            rkind = 'tool'
                                except Exception:
                                    pass
                            out['running_kind'] = rkind
                            if st_at:
                                out['running_started_at'] = str(st_at)
                except Exception:
                    pass
            finally:
                conn.close()
        except Exception:
            out.setdefault('phase', '')
            out.setdefault('heartbeat', '')
            out.setdefault('last_step_at', '')
            out.setdefault('running_kind', '')
            out.setdefault('running_started_at', '')
            out.setdefault('last_node', '')
            out.setdefault('last_io_call', {})
            out.setdefault('last_io_out_preview', '')
        return out

    while True:
        # Timeout handling (None or <=0 => infinite)
        now = asyncio.get_event_loop().time()
        if timeout_sec is not None and timeout_sec > 0 and (now - start) > timeout_sec:
            return

        # scan workers and read minimal state
        for dbp in _list_workers():
            wn = dbp.stem.replace('worker_', '', 1)
            cur = _read_state(dbp, wn)
            prev = last_snap.get(wn)
            # Emit on any change of keys
            keys = ('phase','heartbeat','last_step_at','running_kind','running_started_at','last_node','last_io_out_preview')
            if prev is None or any(cur.get(k) != prev.get(k) for k in keys):
                last_snap[wn] = cur
                payload = {
                    'worker_name': wn,
                    'phase': cur.get('phase') or '',
                    'heartbeat': cur.get('heartbeat') or '',
                    'last_step_at': cur.get('last_step_at') or '',
                    'running_kind': cur.get('running_kind') or '',
                    'running_started_at': cur.get('running_started_at') or '',
                    'last_node': cur.get('last_node') or '',
                    'last_io_call': cur.get('last_io_call') or {},
                    'last_io_out_preview': cur.get('last_io_out_preview') or '',
                }
                try:
                    line = (json.dumps(payload, ensure_ascii=False) + "\n").encode('utf-8')
                except Exception:
                    line = (str(payload).replace("\n"," ") + "\n").encode('utf-8', errors='ignore')
                yield line
                sent += 1
                if max_events and sent >= max_events:
                    return
        # light pause
        await _sleep(0.8)

async def stream_ndjson(timeout_sec: float = 0.0, max_events: int = 0):
    from fastapi.responses import StreamingResponse
    # Interprétation: timeout_sec <= 0 => infini (None)
    timeout = None if (timeout_sec is None or timeout_sec <= 0) else float(timeout_sec)
    return StreamingResponse(_gen_stream(timeout, max_events), media_type="application/x-ndjson")

 
 
 
 
 
 
 
 
 
 
