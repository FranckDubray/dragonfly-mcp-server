
from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="INIT",
    entry="STEP_GET_NOW",
    exits={"success": "INIT_DONE"}
)

@step
def STEP_GET_NOW(worker, cycle, env):
    # Get current time (let the tool choose defaults)
    out = env.tool("date", operation="now")
    # Tolerant extraction: handle nested result objects
    val = out.get("result")
    if isinstance(val, dict):
        val = val.get("result") or val.get("iso") or val.get("datetime")
    if not isinstance(val, str) or not val:
        alt = out.get("content") or out.get("datetime") or out.get("iso") or out.get("now")
        if isinstance(alt, dict):
            alt = alt.get("result") or alt.get("iso") or alt.get("datetime")
        if isinstance(alt, str):
            val = alt
        elif alt is not None:
            val = str(alt)
        else:
            val = ""
    if not isinstance(val, str) or not val:
        raise RuntimeError("INIT.STEP_GET_NOW: date.now returned no result")
    cycle.setdefault("dates", {})["now"] = val
    return Next("STEP_TO_STRICT_ISO")

@step
def STEP_TO_STRICT_ISO(worker, cycle, env):
    # Format 'now' to strict ISO 'YYYY-MM-DDTHH:%M:%S'
    now = cycle.get("dates", {}).get("now")
    if not isinstance(now, str) or not now:
        raise RuntimeError("INIT.STEP_TO_STRICT_ISO: missing 'now'")
    out = env.tool("date", operation="format", datetime=now, format="%Y-%m-%dT%H:%M:%S")
    val = (
        out.get("result")
        or out.get("content")
        or out.get("datetime")
        or out.get("iso")
    )
    if not isinstance(val, str) or not val:
        raise RuntimeError("INIT.STEP_TO_STRICT_ISO: date.format returned no result")
    cycle["dates"]["now"] = val
    return Next("STEP_COMPUTE_FROM")

@step
def STEP_COMPUTE_FROM(worker, cycle, env):
    # Compute FROM = now - 3 days using strict input_format
    now = cycle.get("dates", {}).get("now")
    if not isinstance(now, str) or not now:
        raise RuntimeError("INIT.STEP_COMPUTE_FROM: missing 'now'")
    out = env.tool("date", operation="add", datetime=now, input_format="%Y-%m-%dT%H:%M:%S", days=-3)
    val = out.get("result") or out.get("content")
    if not isinstance(val, str) or not val:
        raise RuntimeError("INIT.STEP_COMPUTE_FROM: date.add returned no result")
    cycle["dates"]["from"] = val
    return Next("STEP_ENSURE_VALIDATION_TABLE")

@step
def STEP_ENSURE_VALIDATION_TABLE(worker, cycle, env):
    env.tool("sqlite_db", operation="execute", db=worker.get("db_file"),
             query=("CREATE TABLE IF NOT EXISTS validation_logs ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "timestamp TEXT NOT NULL,"
                    "attempt INTEGER,"
                    "score REAL,"
                    "feedback TEXT,"
                    "top10_json TEXT)"))
    return Next("STEP_ENSURE_REPORTS_TABLE")

@step
def STEP_ENSURE_REPORTS_TABLE(worker, cycle, env):
    env.tool("sqlite_db", operation="execute", db=worker.get("db_file"),
             query=("CREATE TABLE IF NOT EXISTS reports ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    "date_from TEXT,"
                    "date_to TEXT,"
                    "report_markdown TEXT,"
                    "avg_score REAL,"
                    "retry_count INTEGER,"
                    "top10_json TEXT,"
                    "completed_at TEXT)"))
    return Exit("success")
