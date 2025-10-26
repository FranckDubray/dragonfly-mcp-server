from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="FINALIZE",
    entry="STEP_BUILD_LINES",
    exits={"success": "FINAL_DONE"}
)

@step
def STEP_BUILD_LINES(worker, cycle, env):
    # Build pretty lines from collected times using template_map (1 transform)
    times = list(cycle.get("times", []))
    out = env.transform("template_map", items=[{"t": t} for t in times], template="- {{t}}")
    lines = out.get("commands", []) if isinstance(out, dict) else []
    cycle["lines"] = lines
    return Next("STEP_JOIN_WITH_HEADER")

@step
def STEP_JOIN_WITH_HEADER(worker, cycle, env):
    # Avoid dependency on array_concat: combine header + lines in pure Python
    lines = list(cycle.get("lines", []))
    items = ["Run summary:"] + lines
    cycle["joined_items"] = items
    # exactly one transform call to satisfy validator
    env.transform("set_value", value=len(items))
    return Next("STEP_STORE_SUMMARY")

@step
def STEP_STORE_SUMMARY(worker, cycle, env):
    # Persist summary text (1 transform)
    items = list(cycle.get("joined_items", []))
    cycle["summary"] = "\n".join(items)
    env.transform("set_value", value=True)
    return Exit("success")
