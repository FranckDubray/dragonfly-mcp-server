









from __future__ import annotations
from typing import Dict, Any, List, Optional
import sqlite3
import datetime as _dt

def _db_path(worker_name: str) -> str:
  from src.tools._py_orchestrator.api_spawn import db_path_for_worker
  return db_path_for_worker(worker_name)

def _normalize_ts(ts: Optional[str]) -> str:
  try:
    s = str(ts or '').strip()
    if not s:
      return ''
    # Normalize space to 'T'
    if 'T' not in s and ' ' in s:
      s = s.replace(' ', 'T', 1)
    # If no timezone info, append 'Z' to hint UTC
    if 'Z' in s or '+' in s[10:] or '-' in s[10:]:
      return s
    return s + 'Z'
  except Exception:
    return str(ts or '')

def _seconds_between(st: Optional[str], fin: Optional[str]) -> int:
  try:
    if not st or not fin:
      return 0
    a = str(st).strip().replace(' ', 'T')
    b = str(fin).strip().replace(' ', 'T')
    # Map Z to +00:00 for fromisoformat
    if a.endswith('Z'):
      a = a[:-1] + '+00:00'
    if b.endswith('Z'):
      b = b[:-1] + '+00:00'
    da = _dt.datetime.fromisoformat(a)
    db = _dt.datetime.fromisoformat(b)
    return max(0, int((db - da).total_seconds()))
  except Exception:
    return 0

async def list_runs(worker_name: str, limit: int = 20) -> Dict[str, Any]:
  """
  Return recent runs with optional metadata for nicer UI labels.
  - Legacy compatibility: keep "runs": [run_id, ...]
  - New: "runs_meta": [{id, started_at, finished_at, steps, duration_sec, final_status}]
  """
  dbp = _db_path(worker_name)
  conn = sqlite3.connect(dbp, timeout=3.0)
  try:
    # Group by run_id and compute window + count
    cur = conn.execute(
      """
      SELECT
        run_id,
        MIN(COALESCE(started_at, finished_at)) AS started_at,
        MAX(COALESCE(finished_at, started_at)) AS finished_at,
        COUNT(1) AS steps,
        MAX(rowid) AS rid
      FROM job_steps
      WHERE COALESCE(run_id,'')<>''
      GROUP BY run_id
      ORDER BY rid DESC
      LIMIT ?
      """,
      (int(limit),)
    )
    rows = cur.fetchall()
    # Legacy list
    runs: List[str] = [r[0] for r in rows if r and r[0]]
    # Metadata (for pretty labels)
    runs_meta: List[Dict[str, Any]] = []
    for r in rows:
      try:
        rid, st, fin, cnt, _ = r
        # Final status for run = status of last row in this run
        final_status = ''
        try:
          c2 = conn.execute("SELECT status FROM job_steps WHERE run_id=? ORDER BY rowid DESC LIMIT 1", (rid,))
          row2 = c2.fetchone()
          if row2 and row2[0]:
            final_status = str(row2[0])
        except Exception:
          final_status = ''
        stn = _normalize_ts(st)
        finn = _normalize_ts(fin)
        dur = _seconds_between(stn, finn)
        runs_meta.append({
          "id": rid,
          "started_at": stn,
          "finished_at": finn,
          "steps": int(cnt or 0),
          "duration_sec": dur,
          "final_status": final_status,
        })
      except Exception:
        # best-effort: fallback minimal
        runs_meta.append({"id": r[0], "started_at": "", "finished_at": "", "steps": 0, "duration_sec": 0, "final_status": ""})
    return {"accepted": True, "status": "ok", "runs": runs, "runs_meta": runs_meta}
  finally:
    try: conn.close()
    except Exception: pass

async def get_steps(worker_name: str, run_id: Optional[str] = None, limit: int = 500) -> Dict[str, Any]:
  dbp = _db_path(worker_name)
  conn = sqlite3.connect(dbp, timeout=3.0)
  try:
    if run_id:
      cur = conn.execute(
        "SELECT node, status, duration_ms, details_json, finished_at FROM job_steps WHERE run_id=? ORDER BY rowid ASC LIMIT ?",
        (run_id, int(limit))
      )
    else:
      cur = conn.execute(
        "SELECT node, status, duration_ms, details_json, finished_at FROM job_steps ORDER BY rowid ASC LIMIT ?",
        (int(limit),)
      )
    steps: List[Dict[str, Any]] = []
    import json
    for node, st, dur, dj, fin in cur.fetchall():
      rec = {"node": node, "status": st, "duration_ms": int(dur or 0), "finished_at": _normalize_ts(fin)}
      if dj:
        try:
          obj = json.loads(dj)
          rec["io"] = {"in": obj.get("call") or {}, "out_preview": obj.get("last_result_preview")}
        except Exception:
          rec["io"] = {"in": {}, "out_preview": ""}
      steps.append(rec)
    return {"accepted": True, "status": "ok", "steps": steps}
  finally:
    try: conn.close()
    except Exception: pass

 
