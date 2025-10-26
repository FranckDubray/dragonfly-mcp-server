


from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="VALIDATE",
    entry="STEP_GET_TS",
    exits={"success": "VAL_DONE", "retry": "VAL_RETRY", "retry_exhausted": "VAL_EXHAUSTED"}
)

@step
def STEP_GET_TS(worker, cycle, env):
    out = env.tool("date", operation="now", format="iso", timezone="UTC")
    cycle.setdefault("validation", {})["timestamp"] = out.get("result") or out.get("content") or str(out)
    return Next("STEP_SONAR_VALIDATE")

@step
def STEP_SONAR_VALIDATE(worker, cycle, env):
    prompts = worker.get("prompts", {})
    tpl = str(prompts.get("validate_json") or "")
    messages = [{"role": "user", "content": tpl}]
    out = env.tool("call_llm", model=worker.get("sonar_model"), messages=messages, temperature=0.1, response_format="json")
    cycle.setdefault("validation", {})["raw"] = out.get("content") or out.get("result") or "{}"
    return Next("STEP_NORMALIZE")

@step
def STEP_NORMALIZE(worker, cycle, env):
    raw = cycle.get("validation", {}).get("raw")
    out = env.transform("normalize_llm_output", content=raw)
    cycle["validation"]["parsed"] = out.get("parsed") or {}
    return Next("STEP_EXTRACT_SCORE")

@step
def STEP_EXTRACT_SCORE(worker, cycle, env):
    parsed = cycle.get("validation", {}).get("parsed")
    out = env.transform("json_ops", op="get", data=parsed, path="score", default=None)
    cycle["validation"]["score_raw"] = out.get("result")
    return Next("STEP_COERCE_SCORE")

@step
def STEP_COERCE_SCORE(worker, cycle, env):
    out = env.transform("coerce_number", value=cycle.get("validation", {}).get("score_raw"), default=0.0)
    cycle["validation"]["score"] = out.get("number", 0.0)
    return Next("STEP_EXTRACT_FEEDBACK")

@step
def STEP_EXTRACT_FEEDBACK(worker, cycle, env):
    parsed = cycle.get("validation", {}).get("parsed")
    out = env.transform("json_ops", op="get", data=parsed, path="feedback", default="No feedback")
    cycle["validation"]["feedback"] = out.get("result")
    return Next("STEP_PREP_LOG_PARAMS")

# Nouveau: PREP avant INSERT → transforme les params en strings
@step
def STEP_PREP_LOG_PARAMS(worker, cycle, env):
    v = cycle.get("validation", {})
    params = [
        v.get("timestamp") or "",
        int(cycle.get("meta", {}).get("retry_count", 0)),
        float(v.get("score") or 0.0),
        str(v.get("feedback") or ""),
        cycle.get("scoring", {}).get("top10_json") or "[]",
    ]
    out = env.transform("to_text_list", items=params)
    cycle["validation"]["log_params"] = out.get("items") or []
    return Next("STEP_LOG_DB")

@step
def STEP_LOG_DB(worker, cycle, env):
    env.tool(
        "sqlite_db", operation="execute", db=worker.get("db_file"),
        query=("INSERT INTO validation_logs (timestamp, attempt, score, feedback, top10_json) VALUES (?, ?, ?, ?, ?)"),
        params=cycle.get("validation", {}).get("log_params", [])
    )
    return Next("STEP_LOAD_THRESHOLD")

@step
def STEP_LOAD_THRESHOLD(worker, cycle, env):
    out = env.transform("set_value", value=worker.get("quality_threshold", 7))
    cycle.setdefault("validation", {})["threshold"] = out.get("result")
    return Next("COND_THRESHOLD")

@cond
def COND_THRESHOLD(worker, cycle, env):
    score = float(cycle.get("validation", {}).get("score") or 0.0)
    thr = float(cycle.get("validation", {}).get("threshold") or 7.0)
    if score >= thr:
        return Exit("success")
    return Next("STEP_INC_RETRY")

@step
def STEP_INC_RETRY(worker, cycle, env):
    rc = int(cycle.setdefault("meta", {}).get("retry_count", 0)) + 1
    out = env.transform("set_value", value=rc)
    cycle["meta"]["retry_count"] = out.get("result")
    return Next("COND_RETRY_LEFT")

@cond
def COND_RETRY_LEFT(worker, cycle, env):
    rc = int(cycle.get("meta", {}).get("retry_count", 0))
    mr = int(worker.get("max_retries", 3))
    if rc < mr:
        return Exit("retry")
    return Exit("retry_exhausted")

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 