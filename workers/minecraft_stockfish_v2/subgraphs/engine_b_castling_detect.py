



























from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="ENGINE_B_CASTLING_DETECT",
    entry="ENG_CD_KS_START",
    exits={"success": "DT_EXIT_OK"}
)

@cond
def ENG_CD_KS_START(worker, cycle, env):
    best = str(cycle.get("eng", {}).get("best_uci") or "")
    if best.startswith("e8g8"):
        return Next("STEP_SET_SIDE_KS")
    return Next("COND_QS")

@cond
def COND_QS(worker, cycle, env):
    best = str(cycle.get("eng", {}).get("best_uci") or "")
    if best.startswith("e8c8"):
        return Next("STEP_SET_SIDE_QS")
    return Next("STEP_CLEAR_SIDE")

@step
def STEP_SET_SIDE_KS(worker, cycle, env):
    out = env.transform("set_value", value="ks")
    cycle.setdefault("eng", {})["_castle_side"] = out.get("result")
    return Next("DT_EXIT_OK")

@step
def STEP_SET_SIDE_QS(worker, cycle, env):
    out = env.transform("set_value", value="qs")
    cycle.setdefault("eng", {})["_castle_side"] = out.get("result")
    return Next("DT_EXIT_OK")

@step
def STEP_CLEAR_SIDE(worker, cycle, env):
    out = env.transform("set_value", value="")
    cycle.setdefault("eng", {})["_castle_side"] = out.get("result")
    return Next("DT_EXIT_OK")

@step
def DT_EXIT_OK(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
