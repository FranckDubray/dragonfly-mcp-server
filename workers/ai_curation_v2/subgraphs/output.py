from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="OUTPUT",
    entry="STEP_LLM_FORMAT_FR",
    exits={"success": "OUT_DONE"}
)

@step
def STEP_LLM_FORMAT_FR(worker, cycle, env):
    top10 = cycle.get("scoring", {}).get("top10", [])
    val = {
        "score": float(cycle.get("validation", {}).get("score") or 0.0),
        "retry_count": int(cycle.get("meta", {}).get("retry_count", 0))
    }
    msg = (
        "IMPÉRATIF : Réponds UNIQUEMENT en français. Génère un rapport markdown Top 10 IA/LLM.\n\n"
        f"Top10 JSON: {str(top10)[:4000]}\n"
        f"Validation: {str(val)}\n"
    )
    out = env.tool(
        "call_llm",
        model=worker.get("llm_model"),
        messages=[{"role":"user","content": msg}],
        temperature=0.3,
        response_format="text"
    )
    content = out.get("content") or out.get("result") or ""
    if not isinstance(content, str):
        content = str(content)
    cycle.setdefault("result", {})["report_markdown"] = content
    return Next("STEP_COMPLETION_TS")

@step
def STEP_COMPLETION_TS(worker, cycle, env):
    out = env.tool("date", operation="now", format="iso", tz="UTC")
    cycle.setdefault("result", {})["completed_at"] = out.get("result") or out.get("content") or ""
    return Next("STEP_GET_RUN_WORKER_NAME")

@step
def STEP_GET_RUN_WORKER_NAME(worker, cycle, env):
    q = env.tool(
        "sqlite_db", operation="query", db=worker.get("db_file"),
        query="SELECT svalue FROM job_state_kv WHERE skey='worker_name' LIMIT 1"
    )
    rows = q.get("rows") or []
    worker_name = rows[0].get("svalue") if rows and isinstance(rows[0], dict) else None
    cycle.setdefault("audit", {})["worker_name"] = worker_name or ""
    return Next("STEP_GET_RUN_PID")

@step
def STEP_GET_RUN_PID(worker, cycle, env):
    q = env.tool(
        "sqlite_db", operation="query", db=worker.get("db_file"),
        query="SELECT svalue FROM job_state_kv WHERE skey='pid' LIMIT 1"
    )
    rows = q.get("rows") or []
    pid = rows[0].get("svalue") if rows and isinstance(rows[0], dict) else None
    cycle.setdefault("audit", {})["pid"] = pid or ""
    return Next("STEP_GEN_RUN_ID")

@step
def STEP_GEN_RUN_ID(worker, cycle, env):
    ts_out = env.tool("date", operation="now", format="%Y-%m-%dT%H:%M:%S.%fZ", tz="UTC")
    ts_run = ts_out.get("result") or ""
    pid = cycle.get("audit", {}).get("pid") or ""
    run_id = f"{pid}-{ts_run}" if pid else ts_run
    a = cycle.setdefault("audit", {})
    a["ts_run"] = ts_run
    a["run_id"] = run_id
    return Next("STEP_ENSURE_AUDIT_TABLE")

@step
def STEP_ENSURE_AUDIT_TABLE(worker, cycle, env):
    env.tool(
        "sqlite_db", operation="execute", db=worker.get("db_file"),
        query=("CREATE TABLE IF NOT EXISTS report_audit ("
               "run_id TEXT, ts TEXT, worker_name TEXT, pid TEXT, phase TEXT,"
               "config_json TEXT, report_count_after INTEGER)")
    )
    return Next("STEP_BUILD_CFG_JSON")

@step
def STEP_BUILD_CFG_JSON(worker, cycle, env):
    dates = cycle.get("dates", {})
    cfg = {
        "from": str(dates.get("from") or ""),
        "to": str(dates.get("now") or ""),
        "llm_model": worker.get("llm_model"),
        "quality_threshold": worker.get("quality_threshold"),
        "providers_news": ["guardian"],
        "primary_sites": worker.get("primary_sites", []),
    }
    out = env.transform("json_stringify", value=cfg)
    cycle.setdefault("audit", {})["cfg_json"] = out.get("json_string") or "{}"
    return Next("STEP_INSERT_REPORT")

@step
def STEP_INSERT_REPORT(worker, cycle, env):
    dates = cycle.get("dates", {})
    md = cycle.get("result", {}).get("report_markdown") or ""
    if not isinstance(md, str):
        md = str(md)
    t10 = cycle.get("scoring", {}).get("top10_json") or "[]"
    if not isinstance(t10, str):
        t10 = str(t10)
    env.tool(
        "sqlite_db", operation="execute", db=worker.get("db_file"),
        query=("INSERT INTO reports (date_from, date_to, report_markdown, avg_score, retry_count, top10_json, completed_at) "
               "VALUES (?, ?, ?, ?, ?, ?, ?)"),
        params=[
            str(dates.get("from") or ""),
            str(dates.get("now") or ""),
            md,
            float(cycle.get("validation", {}).get("score") or 0.0),
            int(cycle.get("meta", {}).get("retry_count", 0)),
            t10,
            str(cycle.get("result", {}).get("completed_at") or "")
        ]
    )
    return Next("STEP_COUNT_REPORTS")

@step
def STEP_COUNT_REPORTS(worker, cycle, env):
    q = env.tool("sqlite_db", operation="query", db=worker.get("db_file"), query="SELECT COUNT(*) AS n FROM reports")
    rows = q.get("rows") or []
    count_after = 0
    if rows and isinstance(rows[0], dict):
        n_val = rows[0].get("n")
        n_str = str(n_val) if n_val is not None else "0"
        count_after = int(n_str) if n_str.isdigit() else 0
    cycle.setdefault("audit", {})["count_after"] = count_after
    return Next("STEP_SELECT_PHASE")

@step
def STEP_SELECT_PHASE(worker, cycle, env):
    q = env.tool("sqlite_db", operation="query", db=worker.get("db_file"),
                 query="SELECT svalue FROM job_state_kv WHERE skey='phase' LIMIT 1")
    rows = q.get("rows") or []
    phase = rows[0].get("svalue") if rows and isinstance(rows[0], dict) else ""
    cycle.setdefault("audit", {})["phase"] = phase or ""
    return Next("STEP_INSERT_AUDIT")

@step
def STEP_INSERT_AUDIT(worker, cycle, env):
    a = cycle.get("audit", {})
    env.tool(
        "sqlite_db", operation="execute", db=worker.get("db_file"),
        query=("INSERT INTO report_audit (run_id, ts, worker_name, pid, phase, config_json, report_count_after)"
               " VALUES (?, ?, ?, ?, ?, ?, ?)"),
        params=[
            a.get("run_id") or "",
            a.get("ts_run") or "",
            a.get("worker_name") or "",
            a.get("pid") or "",
            a.get("phase") or "",
            a.get("cfg_json") or "{}",
            int(a.get("count_after") or 0)
        ]
    )
    # Résumé final
    top10 = cycle.get("scoring", {}).get("top10") or []
    n = len(top10) if isinstance(top10, list) else 0
    score = float(cycle.get("validation", {}).get("score") or 0.0)
    retry_count = int(cycle.get("meta", {}).get("retry_count", 0))
    completed_at = cycle.get("result", {}).get("completed_at") or ""
    run_id = a.get("run_id") or ""
    summary = (
        f"Rapport IA/LLM — items: {n}, score: {score:.2f}, retries: {retry_count}, date: {completed_at}\n"
        f"(reports COUNT after insert: {int(a.get('count_after') or 0)}, run_id: {run_id})\n"
        "(Voir table reports pour le markdown complet)"
    )
    cycle["summary"] = summary
    return Exit("success")
