from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="RETRY",
    entry="STEP_TRY",
    exits={"success": "RETRY_DONE"}
)

@step
def STEP_TRY(worker, cycle, env):
    # Retry loop: increment attempts until reaching retry_count, then succeed
    attempts = int(cycle.get("attempts", 0))
    need = int(cycle.get("retry_count", 2))
    cycle["attempts"] = attempts + 1
    # Exactly one transform call to comply with validator
    env.transform("set_value", value=f"attempt_{attempts+1}")
    return Next("COND_AGAIN")

@cond
def COND_AGAIN(worker, cycle, env):
    attempts = int(cycle.get("attempts", 0))
    need = int(cycle.get("retry_count", 2))
    if attempts < need:
        return Next("STEP_TRY")
    return Exit("success")
