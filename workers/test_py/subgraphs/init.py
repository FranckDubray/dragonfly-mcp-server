from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="INIT",
    entry="STEP_INIT",
    exits={"success": "INIT_DONE"}
)

@step
def STEP_INIT(worker, cycle, env):
    # Initialize loop state
    cycle["times"] = []
    cycle["counter"] = 0
    cycle["limit"] = 3
    # One required transform call per step
    env.transform("set_value", value="init")
    return Next("STEP_READY")

@step
def STEP_READY(worker, cycle, env):
    # Use a generic transform to keep validation strict
    env.transform("set_value", value="ready")
    return Exit("success")
