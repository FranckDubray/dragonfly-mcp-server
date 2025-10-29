



























from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="WHITE_WN_CASTLING_DETECT",
    entry="WN_CD_KS_START",
    exits={"success": "DT_EXIT_OK"}
)

@cond
def WN_CD_KS_START(worker, cycle, env):
    uci = str(cycle.get("move", {}).get("uci") or "")
    if uci.startswith("e1g1"):
        return Next("STEP_SET_SIDE_KS")
    return Next("COND_QS")

@cond
def COND_QS(worker, cycle, env):
    uci = str(cycle.get("move", {}).get("uci") or "")
    if uci.startswith("e1c1"):
        return Next("STEP_SET_SIDE_QS")
    return Next("STEP_CLEAR_SIDE")

@step
def STEP_SET_SIDE_KS(worker, cycle, env):
    out = env.transform("set_value", value="ks")
    cycle.setdefault("wn", {})["_castle_side"] = out.get("result")
    return Next("DT_EXIT_OK")

@step
def STEP_SET_SIDE_QS(worker, cycle, env):
    out = env.transform("set_value", value="qs")
    cycle.setdefault("wn", {})["_castle_side"] = out.get("result")
    return Next("DT_EXIT_OK")

@step
def STEP_CLEAR_SIDE(worker, cycle, env):
    out = env.transform("set_value", value="")
    cycle.setdefault("wn", {})["_castle_side"] = out.get("result")
    return Next("DT_EXIT_OK")

@step
def DT_EXIT_OK(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 