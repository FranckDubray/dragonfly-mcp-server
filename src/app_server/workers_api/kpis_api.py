

















from __future__ import annotations
from typing import Dict, Any
import sqlite3
from pathlib import Path
import json

# KPIs aggregation v2: count workers, actifs, real steps in the last 24h across worker_*.db
# NOW adds tokens24h by summing usage from job_steps.details_json over last 24h

async def get_kpis() -> Dict[str, Any]:
    from src.app_server.workers_api.list_api import get_list
    from src.tools._py_orchestrator.api_common import SQLITE_DIR

    lst = await get_list()
    ws = lst.get("workers", []) if isinstance(lst, dict) else []

    actifs = 0
    for w in ws:
        ph = str((w.get("status") or "")).lower()
        if ph in {"starting", "running"}:
            actifs += 1

    steps24h_total = 0
    tokens24h_total = 0
    try:
        base = Path(SQLITE_DIR)
        for dbp in base.glob("worker_*.db"):
            try:
                conn = sqlite3.connect(str(dbp), timeout=2.0)
                try:
                    # steps in last 24h
                    cur = conn.execute(
                        "SELECT COUNT(1) FROM job_steps WHERE COALESCE(finished_at, started_at) >= datetime('now','-1 day')"
                    )
                    row = cur.fetchone()
                    steps24h_total += int(row[0] or 0)

                    # tokens in last 24h (try JSON1, else python fallback)
                    added = 0
                    try:
                        cur = conn.execute(
                            """
                            SELECT COALESCE(SUM(
                              CAST(
                                COALESCE(
                                  json_extract(details_json,'$.usage.total_tokens'),
                                  json_extract(details_json,'$.usage.prompt_tokens') + json_extract(details_json,'$.usage.completion_tokens'),
                                  json_extract(details_json,'$.usage.input_tokens')   + json_extract(details_json,'$.usage.output_tokens')
                                ) AS INTEGER)
                            ), 0)
                            FROM job_steps
                            WHERE COALESCE(finished_at, started_at) >= datetime('now','-1 day')
                              AND (
                                json_extract(details_json,'$.usage.total_tokens') IS NOT NULL
                                OR json_extract(details_json,'$.usage.prompt_tokens') IS NOT NULL
                                OR json_extract(details_json,'$.usage.input_tokens') IS NOT NULL
                              )
                            """
                        )
                        row = cur.fetchone()
                        added = int(row[0] or 0)
                    except Exception:
                        # Fallback parsing in Python if JSON1 not available
                        try:
                            cur = conn.execute(
                                "SELECT details_json FROM job_steps WHERE COALESCE(finished_at, started_at) >= datetime('now','-1 day') AND details_json IS NOT NULL"
                            )
                            for (dj,) in cur.fetchall():
                                try:
                                    obj = json.loads(dj)
                                except Exception:
                                    continue
                                u = obj.get("usage") or {}
                                if isinstance(u, dict):
                                    total = None
                                    if "total_tokens" in u:
                                        total = u.get("total_tokens")
                                    elif "prompt_tokens" in u or "completion_tokens" in u:
                                        total = (u.get("prompt_tokens") or 0) + (u.get("completion_tokens") or 0)
                                    elif "input_tokens" in u or "output_tokens" in u:
                                        total = (u.get("input_tokens") or 0) + (u.get("output_tokens") or 0)
                                    if total:
                                        added += int(total or 0)
                        except Exception:
                            pass
                    tokens24h_total += added
                finally:
                    conn.close()
            except Exception:
                # skip this DB, continue
                continue
    except Exception:
        # on global error, keep counters at 0 rather than None
        pass

    return {
        "accepted": True,
        "status": "ok",
        "workers": len(ws),
        "actifs": actifs,
        "steps24h": steps24h_total,
        "tokens24h": tokens24h_total,
        "qualite7j": None,
    }

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
