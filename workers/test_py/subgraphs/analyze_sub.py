from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="AN_SUB",
    entry="STEP_SUB_PREP",
    exits={"success": "AN_SUB_DONE"}
)

@step
def STEP_SUB_PREP(worker, cycle, env):
    # One transform to comply
    env.transform("set_value", value="sub_prep")
    return Next("STEP_SUB_FINISH")

@step
def STEP_SUB_FINISH(worker, cycle, env):
    env.transform("set_value", value="sub_finish")
    return Exit("success")
