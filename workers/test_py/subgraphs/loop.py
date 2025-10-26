from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="LOOP",
    entry="STEP_TICK_TOOL",
    exits={"success": "LOOP_DONE", "maxed": "LOOP_MAX"}
)

@step
def STEP_TICK_TOOL(worker, cycle, env):
    # Call MCP tool 'date' (no system libs)
    res = env.tool("date", operation="now", tz="UTC")
    # Prefer standard 'result' (ISO8601), fallback defensively
    t = res.get("result") or res.get("datetime") or res.get("date") or str(res)
    cycle.setdefault("times", []).append(t)
    cycle["last_time"] = t
    return Next("STEP_SAVE_TIME")

@step
def STEP_SAVE_TIME(worker, cycle, env):
    # exactly one transform call
    env.transform("set_value", value=str(cycle.get("last_time", "")))
    return Next("COND_CONTINUE")

@cond
def COND_CONTINUE(worker, cycle, env):
    # Decide to continue or exit
    cnt = int(cycle.get("counter", 0))
    limit = int(cycle.get("limit", 3))
    if cnt + 1 >= limit:
        return Exit("maxed")
    return Next("STEP_INCR")

@step
def STEP_INCR(worker, cycle, env):
    # increment and continue the loop
    cycle["counter"] = int(cycle.get("counter", 0)) + 1
    env.transform("set_value", value=cycle["counter"])
    return Next("STEP_TICK_TOOL")
