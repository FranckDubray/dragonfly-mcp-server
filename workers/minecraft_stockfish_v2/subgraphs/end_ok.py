


from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="END_OK",
    entry="STEP_DONE",
    exits={"success": "END"}
)

@step
def STEP_DONE(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")
