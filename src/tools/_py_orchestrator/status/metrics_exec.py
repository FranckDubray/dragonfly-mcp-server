
import json
from typing import Any, Dict, List
from .parts.safe_db import safe_query


def metrics_current_run(db_path: str, worker: str, minutes_fallback: int = 60) -> Dict[str, Any]:
    nodes_executed = 0
    sum_duration = 0
    count_duration = 0
    errors = {"io": 0, "validation": 0, "permission": 0, "timeout": 0}
    retries_attempts = 0
    nodes_with_retries = set()

    # run_started_at is used by caller; if absent we still return zeroed metrics
    rows = safe_query(
        db_path,
        "SELECT node, status, duration_ms, details_json FROM job_steps WHERE worker=? ORDER BY rowid DESC LIMIT ?",
        (worker, 200),
    )
    for r in rows:
        duration_ms = r[2] if isinstance(r, tuple) else r["duration_ms"]
        nodes_executed += 1
        try:
            dm = int(duration_ms)
            if dm >= 0:
                sum_duration += dm
                count_duration += 1
        except Exception:
            pass
    avg_duration = int(sum_duration / count_duration) if count_duration > 0 else 0
    return {
        "window": "run",
        "nodes_executed": nodes_executed,
        "avg_duration_ms": avg_duration,
        "errors": errors,
        "retries": {"attempts": retries_attempts, "nodes_with_retries": len(nodes_with_retries)},
        "llm_tokens": 0,
        "token_llm": {},
    }


def recent_steps(db_path: str, worker: str, limit: int = 10) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    rows = safe_query(
        db_path,
        "SELECT node, status, duration_ms, details_json FROM job_steps WHERE worker=? ORDER BY rowid DESC LIMIT ?",
        (worker, int(limit)),
    )
    for r in rows:
        node = r[0] if isinstance(r, tuple) else r["node"]
        status = r[1] if isinstance(r, tuple) else r["status"]
        duration_ms = r[2] if isinstance(r, tuple) else r["duration_ms"]
        details_json = r[3] if isinstance(r, tuple) else r.get("details_json")
        rec = {"node": node, "status": status, "duration_ms": duration_ms}
        if details_json:
            try:
                dj = json.loads(details_json)
                err = dj.get("error", {}) if isinstance(dj, dict) else {}
                call = dj.get("call", {}) if isinstance(dj, dict) else {}
                lrp = dj.get("last_result_preview") if isinstance(dj, dict) else None
                if err:
                    rec["error"] = {"message": str(err.get("message", ""))[:200]}
                if call:
                    rec["call"] = {"kind": call.get("kind"), "name": call.get("name")}
                if lrp is not None:
                    s = lrp if isinstance(lrp, str) else str(lrp)
                    rec["last_result_preview"] = s[:200]
            except Exception:
                pass
        out.append(rec)
    return out


def crash_packet(db_path: str, worker: str) -> Dict[str, Any]:
    rows = safe_query(
        db_path,
        "SELECT ts, cycle_id, node, message FROM crash_logs WHERE worker=? ORDER BY id DESC LIMIT 1",
        (worker,),
    )
    if not rows:
        return {}
    r = rows[0]
    ts = r[0] if isinstance(r, tuple) else r["ts"]
    cycle_id = r[1] if isinstance(r, tuple) else r["cycle_id"]
    node = r[2] if isinstance(r, tuple) else r["node"]
    message = r[3] if isinstance(r, tuple) else r["message"]
    return {"ts": ts, "cycle_id": cycle_id, "node": node, "message": (message or "")[:400]}
