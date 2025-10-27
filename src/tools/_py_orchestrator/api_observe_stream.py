from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json
import time
import sqlite3

from .api_spawn import db_path_for_worker
from .db import get_state_kv
from .api_start import start as start_worker_api

router = APIRouter()

def _sse_pack(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

def _ndjson_pack(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False) + "\n"

def _timeout_parse(val):
    try:
        if val is None:
            return None  # infinite by default
        v = float(val)
        if v <= 0:
            return None
        return min(v, 86400.0)
    except Exception:
        return None

def _max_rowid(dbp: str, worker_name: str, run_id: str) -> int:
    try:
        conn = sqlite3.connect(dbp, timeout=3.0)
        try:
            cur = conn.execute(
                "SELECT COALESCE(MAX(rowid),0) FROM job_steps WHERE worker=? AND (run_id=? OR ?='')",
                (worker_name, run_id, run_id),
            )
            row = cur.fetchone()
            return int(row[0] or 0)
        finally:
            conn.close()
    except Exception:
        return 0

def _rows_since(dbp: str, worker_name: str, run_id: str, last_rowid: int):
    try:
        conn = sqlite3.connect(dbp, timeout=3.0)
        try:
            cur = conn.execute(
                "SELECT rowid, cycle_id, node, status, duration_ms, details_json, finished_at "
                "FROM job_steps WHERE worker=? AND (run_id=? OR ?='') AND rowid>? ORDER BY rowid ASC",
                (worker_name, run_id, run_id, int(last_rowid)),
            )
            return cur.fetchall()
        finally:
            conn.close()
    except Exception:
        return []

def _recent_window(dbp: str, worker_name: str, run_id: str, window: int = 10):
    try:
        conn = sqlite3.connect(dbp, timeout=3.0)
        try:
            cur = conn.execute(
                "SELECT rowid, cycle_id, node, status, duration_ms, details_json, finished_at "
                "FROM job_steps WHERE worker=? AND (run_id=? OR ?='') ORDER BY rowid DESC LIMIT ?",
                (worker_name, run_id, run_id, int(window)),
            )
            return cur.fetchall()
        finally:
            conn.close()
    except Exception:
        return []

async def _observe_stream(worker_name: str, protocol: str, timeout_sec: float | None, max_events: int | None):
    dbp = db_path_for_worker(worker_name)

    run_id = get_state_kv(dbp, worker_name, 'run_id') or ''

    start = time.time()
    sent = 0
    pack = _sse_pack if protocol == "sse" else _ndjson_pack
    tick = 0.2

    last_rowid = _max_rowid(dbp, worker_name, run_id)
    # Track recent row updates: rowid -> signature(status, finished_at, duration_ms, details_json_hash)
    seen_sig: dict[int, tuple] = {}

    while True:
        # terminal or timeout
        phase = get_state_kv(dbp, worker_name, 'phase') or ''
        if phase in {'completed','failed','canceled'}:
            payload = {
                'chunk_type': ('error' if phase == 'failed' else 'step'),
                'node_executed': '',
                'io': {'in': {}, 'out_preview': ''},
                'error': ({'message': get_state_kv(dbp, worker_name, 'last_error') or ''} if phase == 'failed' else None),
                'phase': phase,
                'heartbeat': get_state_kv(dbp, worker_name, 'heartbeat') or '',
                'cycle_id': get_state_kv(dbp, worker_name, 'debug.cycle_id') or '',
                'terminal': True,
            }
            yield pack('error' if (payload['chunk_type']=='error' and protocol=='sse') else 'step', payload)
            return

        # 1) New inserts since last_rowid
        rows = _rows_since(dbp, worker_name, run_id, last_rowid)
        if rows:
            for rid, cycle_id, node, status, dur, dj, fin in rows:
                call = {}
                lrp = ''
                try:
                    if dj:
                        obj = json.loads(dj)
                        if isinstance(obj, dict):
                            call = obj.get('call') or {}
                            lrp_val = obj.get('last_result_preview')
                            if lrp_val is not None:
                                lrp = lrp_val if isinstance(lrp_val, str) else str(lrp_val)
                except Exception:
                    pass
                payload = {
                    'chunk_type': ('error' if str(status).lower()=='failed' else 'step'),
                    'node_executed': node,
                    'io': {'in': call, 'out_preview': lrp},
                    'error': ({'message': (get_state_kv(dbp, worker_name, 'last_error') or '')} if str(status).lower()=='failed' else None),
                    'phase': get_state_kv(dbp, worker_name, 'phase') or '',
                    'heartbeat': get_state_kv(dbp, worker_name, 'heartbeat') or '',
                    'cycle_id': cycle_id,
                    'duration_ms': int(dur or 0),
                }
                yield pack('error' if (payload['chunk_type']=='error' and protocol=='sse') else 'step', payload)
                sent += 1
                last_rowid = int(rid)
                # seed signature cache for updates
                sig = (str(status or ''), str(fin or ''), int(dur or 0), (dj[:120] if isinstance(dj, str) else str(dj)[:120]))
                seen_sig[int(rid)] = sig
                if max_events and sent >= max_events:
                    return
        else:
            await asyncio.sleep(tick)

        # 2) Detect updates on recent window (running -> succeeded/failed, etc.)
        recent = _recent_window(dbp, worker_name, run_id, window=10)
        # iterate in ascending order so we emit in timeline order
        for rid, cycle_id, node, status, dur, dj, fin in reversed(recent):
            rid_i = int(rid)
            # build current signature
            cur_sig = (str(status or ''), str(fin or ''), int(dur or 0), (dj[:120] if isinstance(dj, str) else str(dj)[:120]))
            prev_sig = seen_sig.get(rid_i)
            if prev_sig is None:
                # First time we see this row in the window; don't emit (insert was handled above if applicable)
                seen_sig[rid_i] = cur_sig
                continue
            if cur_sig != prev_sig:
                # emit update chunk
                call = {}
                lrp = ''
                try:
                    if dj:
                        obj = json.loads(dj)
                        if isinstance(obj, dict):
                            call = obj.get('call') or {}
                            lrp_val = obj.get('last_result_preview')
                            if lrp_val is not None:
                                lrp = lrp_val if isinstance(lrp_val, str) else str(lrp_val)
                except Exception:
                    pass
                payload = {
                    'chunk_type': ('error' if str(status).lower()=='failed' else 'step'),
                    'node_executed': node,
                    'io': {'in': call, 'out_preview': lrp},
                    'error': ({'message': (get_state_kv(dbp, worker_name, 'last_error') or '')} if str(status).lower()=='failed' else None),
                    'phase': get_state_kv(dbp, worker_name, 'phase') or '',
                    'heartbeat': get_state_kv(dbp, worker_name, 'heartbeat') or '',
                    'cycle_id': cycle_id,
                    'duration_ms': int(dur or 0),
                    'updated': True,
                }
                yield pack('error' if (payload['chunk_type']=='error' and protocol=='sse') else 'step', payload)
                sent += 1
                seen_sig[rid_i] = cur_sig
                if max_events and sent >= max_events:
                    return

        if (timeout_sec is not None) and ((time.time() - start) > timeout_sec):
            return

@router.get("/tools/py_orchestrator/observe")
async def observe_stream(worker_name: str, protocol: str = "sse", timeout_sec: float | None = None, max_events: int = 0):
    protocol = (protocol or "sse").lower()
    if protocol not in {"sse","ndjson"}:
        protocol = "sse"
    timeout = _timeout_parse(timeout_sec)
    gen = _observe_stream(worker_name=worker_name, protocol=protocol, timeout_sec=timeout, max_events=max_events)
    if protocol == "sse":
        return StreamingResponse(gen, media_type="text/event-stream")
    return StreamingResponse(gen, media_type="application/x-ndjson")

@router.get("/tools/py_orchestrator/start_observe")
async def start_observe(worker_name: str, worker_file: str, protocol: str = "sse", timeout_sec: float | None = None, hot_reload: bool = True):
    # Start the worker, then attach passive observation stream in the same request
    try:
        _ = start_worker_api({'operation': 'start', 'worker_name': worker_name, 'worker_file': worker_file, 'hot_reload': hot_reload})
    except Exception:
        pass
    # give a tiny breath for DB init
    await asyncio.sleep(0.2)
    timeout = _timeout_parse(timeout_sec)
    gen = _observe_stream(worker_name=worker_name, protocol=protocol, timeout_sec=timeout, max_events=0)
    if protocol == "sse":
        return StreamingResponse(gen, media_type="text/event-stream")
    return StreamingResponse(gen, media_type="application/x-ndjson")
