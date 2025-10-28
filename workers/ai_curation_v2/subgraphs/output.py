
from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="OUTPUT",
    entry="STEP_FILTER_TOP10_SQL",
    exits={"success": "OUT_DONE"}
)

@step
def STEP_FILTER_TOP10_SQL(worker, cycle, env):
    # Filter current TOP10 against previous reports' URLs (SQLite JSON1)
    t10 = str((cycle.get("scoring") or {}).get("top10_json") or "[]")
    prev_limit = int(worker.get("max_history_reports", 10))
    q = (
        "SELECT COALESCE(json_group_array(ci.value), '[]') AS arr "
        "FROM json_each(?) AS ci "
        "WHERE COALESCE(json_extract(ci.value,'$.url'),'') NOT IN ("
        "  SELECT DISTINCT COALESCE(json_extract(j.value,'$.url'),'') "
        "  FROM (SELECT top10_json FROM reports ORDER BY id DESC LIMIT ?) r, "
        "       json_each(r.top10_json) AS j "
        "  WHERE json_extract(j.value,'$.url') IS NOT NULL"
        ")"
    )
    out = env.tool(
        "sqlite_db", operation="query", db=worker.get("db_file"),
        query=q, params=[t10, prev_limit]
    )
    rows = out.get("rows") or []
    r0 = dict((rows[:1] or [{}])[0])
    filtered = r0.get("arr") or "[]"
    cycle.setdefault("dedup", {})["filtered_json"] = filtered
    return Next("STEP_PARSE_FILTERED")

@step
def STEP_PARSE_FILTERED(worker, cycle, env):
    # Parse filtered JSON array back to list for downstream formatting
    s = str((cycle.get("dedup", {}) or {}).get("filtered_json") or "[]")
    out = env.transform("normalize_llm_output", content=s, fallback_value=[])
    items = out.get("parsed") or []
    cycle.setdefault("scoring", {})["top10"] = items
    cycle["scoring"]["top10_json"] = s
    return Next("STEP_ENFORCE_WINDOW_FINAL")

@step
def STEP_ENFORCE_WINDOW_FINAL(worker, cycle, env):
    # Final safety: enforce 72h cutoff on published_at (one call only)
    dates = cycle.get("dates", {})
    out = env.transform(
        "array_ops", op="filter",
        items=cycle.get("scoring", {}).get("top10", []),
        predicate={"kind":"date_gte", "path":"published_at", "cutoff":str(dates.get("from") or "")}
    )
    items = out.get("items") or []
    cycle.setdefault("scoring", {})["top10"] = items
    return Next("STEP_STRINGIFY_TOP10_FINAL")

@step
def STEP_STRINGIFY_TOP10_FINAL(worker, cycle, env):
    # Separate step to stringify (to respect 1-call-per-step rule)
    items = cycle.get("scoring", {}).get("top10", [])
    out2 = env.transform("json_stringify", value=items)
    cycle.setdefault("scoring", {})["top10_json"] = out2.get("json_string") or "[]"
    return Next("STEP_LLM_FORMAT_FR")

@step
def STEP_LLM_FORMAT_FR(worker, cycle, env):
    top10 = cycle.get("scoring", {}).get("top10", [])
    val = {
        "score": float(cycle.get("validation", {}).get("score") or 0.0),
        "feedback": str(cycle.get("validation", {}).get("feedback") or ""),
        "retry_count": int(cycle.get("meta", {}).get("retry_count", 0))
    }
    prompts = worker.get("prompts", {})
    tpl = str(prompts.get("output_fr") or "")
    # Remplacements directs pour éviter KeyError via str.format sur les accolades du JSON d'exemple
    top10_str = str(top10)[:4000]
    score_str = f"{val.get('score', 0.0):.2f}"
    feedback_str = val.get("feedback", "")
    msg = (
        tpl.replace("{TOP10}", top10_str)
           .replace("{VALIDATION.score}", score_str)
           .replace("{VALIDATION.feedback}", feedback_str)
    )
    out = env.tool(
        "call_llm",
        model=worker.get("llm_model"),
        messages=[{"role":"user","content": msg}],
        temperature=0.3,
        response_format="text"
    )
    content = out.get("content") or out.get("result") or ""
    content = str(content)
    cycle.setdefault("result", {})["report_markdown"] = content
    return Next("STEP_ENFORCE_FR_FINAL")

@step
def STEP_ENFORCE_FR_FINAL(worker, cycle, env):
    # Francisation complémentaire stricte: pas d'altération des URLs ni des noms propres
    md = str(cycle.get("result", {}).get("report_markdown") or "")
    prompt_fr = (
        "Tu es un réviseur. Reformule en français courant tout le texte suivant SANS modifier les URLs ni traduire les noms propres, modèles, organisations ni domaines.\n"
        "- Remplace les tournures anglaises par des équivalents français.\n"
        "- Ne touche pas aux liens Markdown [..](URL), conserve l'URL exacte.\n\n"
        "TEXTE:\n" + md
    )
    out = env.tool(
        "call_llm",
        model=worker.get("llm_model"),
        messages=[{"role":"user","content": prompt_fr}],
        temperature=0.2,
        response_format="text",
        max_output_tokens=int(worker.get("collect_max_output_tokens", 1000))
    )
    md2 = out.get("content") or out.get("result") or md
    cycle["result"]["report_markdown"] = str(md2)
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
    r0 = (rows[:1] or [{}])[0]
    worker_name = r0.get("svalue") or ""
    cycle.setdefault("audit", {})["worker_name"] = worker_name
    return Next("STEP_GET_RUN_PID")

@step
def STEP_GET_RUN_PID(worker, cycle, env):
    q = env.tool(
        "sqlite_db", operation="query", db=worker.get("db_file"),
        query="SELECT svalue FROM job_state_kv WHERE skey='pid' LIMIT 1"
    )
    rows = q.get("rows") or []
    r0 = (rows[:1] or [{}])[0]
    pid = r0.get("svalue") or ""
    cycle.setdefault("audit", {})["pid"] = pid
    return Next("STEP_GEN_RUN_ID")

@step
def STEP_GEN_RUN_ID(worker, cycle, env):
    ts_out = env.tool("date", operation="now", format="%Y-%m-%dT%H:%M:%S.%fZ", tz="UTC")
    ts_run = ts_out.get("result") or ""
    pid = cycle.get("audit", {}).get("pid") or ""
    run_id = ((pid or '') + '-' + ts_run).lstrip('-')
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
        "primary_sites": list((worker.get("primary_site_caps") or {}).keys()),
    }
    out = env.transform("json_stringify", value=cfg)
    cycle.setdefault("audit", {})["cfg_json"] = out.get("json_string") or "{}"
    return Next("STEP_INSERT_REPORT")

@step
def STEP_INSERT_REPORT(worker, cycle, env):
    dates = cycle.get("dates", {})
    md = cycle.get("result", {}).get("report_markdown") or ""
    md = str(md)
    t10 = cycle.get("scoring", {}).get("top10_json") or "[]"
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
    r0 = (rows[:1] or [{}])[0]
    n = int((r0.get("n") or 0))
    cycle.setdefault("audit", {})["count_after"] = n
    return Next("STEP_SELECT_PHASE")

@step
def STEP_SELECT_PHASE(worker, cycle, env):
    q = env.tool("sqlite_db", operation="query", db=worker.get("db_file"),
                 query="SELECT svalue FROM job_state_kv WHERE skey='phase' LIMIT 1")
    rows = q.get("rows") or []
    r0 = (rows[:1] or [{}])[0]
    phase = r0.get("svalue") or ""
    cycle.setdefault("audit", {})["phase"] = phase
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
    summary = (
        f"Rapport IA/LLM — items: {len(cycle.get('scoring', {}).get('top10', []))}, "
        f"score: {float(cycle.get('validation', {}).get('score') or 0.0):.2f}, "
        f"retries: {int(cycle.get('meta', {}).get('retry_count', 0))}, "
        f"date: {cycle.get('result', {}).get('completed_at') or ''}\n"
        f"(reports COUNT after insert: {int(a.get('count_after') or 0)}, run_id: {a.get('run_id') or ''})\n"
        "(Voir table reports pour le markdown complet)"
    )
    cycle["summary"] = summary
    return Exit("success")
