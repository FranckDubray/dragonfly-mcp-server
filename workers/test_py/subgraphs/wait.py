from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="WAIT",
    entry="STEP_SLEEP",
    exits={"success": "WAIT_DONE"}
)

@step
def STEP_SLEEP(worker, cycle, env):
    # Cooperative wait (checks cancel flag), exactly one transform call
    env.transform("sleep", ms=200)
    return Next("STEP_MARK")

@step
def STEP_MARK(worker, cycle, env):
    cycle["waited"] = True
    env.transform("set_value", value=True)
    return Exit("success")
