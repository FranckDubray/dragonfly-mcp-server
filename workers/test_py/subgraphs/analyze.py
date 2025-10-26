from py_orch import SubGraph, SubGraphRef, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="ANALYZE",
    entry="STEP_FORMAT_TIME",
    exits={"success": "AN_DONE", "warn": "AN_WARN"},
    parts=[SubGraphRef("AN_SUB", module="subgraphs.analyze_sub")]
)

@step
def STEP_FORMAT_TIME(worker, cycle, env):
    # Format last_time to a human-readable form using MCP 'date.format'
    last = cycle.get("last_time") or ""
    env.tool("date", operation="format", datetime=str(last), format="%Y-%m-%d %H:%M:%S%z", tz="UTC")
    return Next("STEP_STORE_FMT")

@step
def STEP_STORE_FMT(worker, cycle, env):
    # Keep exactly one transform call; also record a flag in cycle
    cycle["fmt_flag"] = True
    env.transform("set_value", value=True)
    return Next("COND_DECIDE")

@cond
def COND_DECIDE(worker, cycle, env):
    # Branch depending on presence of a space (date format added a space between date and time)
    # This is a pure Python check (no tools/transforms here)
    if " " in str(cycle.get("last_time") or ""):
        return Next("AN_SUB::STEP_SUB_PREP")  # enter nested subgraph
    return Exit("warn")
