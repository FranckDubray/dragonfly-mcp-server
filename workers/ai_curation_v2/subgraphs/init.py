




from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="INIT",
    entry="STEP_GET_NOW",
    exits={"success": "INIT_DONE"}
)

@step
def STEP_GET_NOW(worker, cycle, env):
    # Get current time in strict ISO format (single call)
    out = env.tool("date", operation="now", format="%Y-%m-%dT%H:%M:%S")
    val = out.get("result") or out.get("content") or out.get("iso") or out.get("datetime") or out.get("now") or ""
    cycle.setdefault("dates", {})["now"] = "" + str(val)
    return Next("STEP_COMPUTE_FROM")

@step
def STEP_COMPUTE_FROM(worker, cycle, env):
    # Compute FROM = now - window (hours from config, default 72) using strict input_format
    window_h = int(worker.get("collect_window_hours", 72))
    # Convert hours to days (floor, at least 1 day), subtract as negative days
    days = -max(1, int(window_h // 24))
    now = "" + str((cycle.get("dates") or {}).get("now") or "")
    out = env.tool("date", operation="add", datetime=now, input_format="%Y-%m-%dT%H:%M:%S", days=days)
    val = out.get("result") or out.get("content") or out.get("datetime") or out.get("iso") or ""
    cycle.setdefault("dates", {})["from"] = "" + str(val)
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
