

from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="WHITE_WN_CASTLING_COORDS",
    entry="STEP_FETCH_SQUARES",
    exits={"success": "CC_EXIT_OK"}
)

@step
def STEP_FETCH_SQUARES(worker, cycle, env):
    out = env.transform("set_value", value=cycle.get("mc", {}).get("board", {}).get("squares", []))
    cycle.setdefault("wn", {})["_squares"] = out.get("result") or []
    return Next("STEP_FILTER_A1_H1_F1_D1")

@step
def STEP_FILTER_A1_H1_F1_D1(worker, cycle, env):
    s = cycle.get("wn", {}).get("_squares", [])
    out = env.transform("set_value", value={"a1": s, "h1": s, "f1": s, "d1": s})
    cycle["wn"]["_sq_map"] = out.get("result")
    return Next("STEP_GET_H1")

@step
def STEP_GET_H1(worker, cycle, env):
    s = cycle.get("wn", {}).get("_sq_map", {}).get("h1", [])
    o = env.transform("array_ops", op="filter", items=s, predicate={"kind":"eq","path":"square","value":"h1"})
    cycle["wn"]["h1_item"] = o.get("items") or []
    return Next("STEP_GET_F1")

@step
def STEP_GET_F1(worker, cycle, env):
    s = cycle.get("wn", {}).get("_sq_map", {}).get("f1", [])
    o = env.transform("array_ops", op="filter", items=s, predicate={"kind":"eq","path":"square","value":"f1"})
    cycle["wn"]["f1_item"] = o.get("items") or []
    return Next("STEP_GET_A1")

@step
def STEP_GET_A1(worker, cycle, env):
    s = cycle.get("wn", {}).get("_sq_map", {}).get("a1", [])
    o = env.transform("array_ops", op="filter", items=s, predicate={"kind":"eq","path":"square","value":"a1"})
    cycle["wn"]["a1_item"] = o.get("items") or []
    return Next("STEP_GET_D1")

@step
def STEP_GET_D1(worker, cycle, env):
    s = cycle.get("wn", {}).get("_sq_map", {}).get("d1", [])
    o = env.transform("array_ops", op="filter", items=s, predicate={"kind":"eq","path":"square","value":"d1"})
    cycle["wn"]["d1_item"] = o.get("items") or []
    return Next("STEP_H1_CX")

@step
def STEP_H1_CX(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("wn", {}).get("h1_item"), path="0.center.x", default=0)
    cycle["wn"]["h1_cx"] = j.get("result")
    return Next("STEP_H1_CY")

@step
def STEP_H1_CY(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("wn", {}).get("h1_item"), path="0.center.y", default=0)
    cycle["wn"]["h1_cy"] = j.get("result")
    return Next("STEP_H1_CZ")

@step
def STEP_H1_CZ(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("wn", {}).get("h1_item"), path="0.center.z", default=0)
    cycle["wn"]["h1_cz"] = j.get("result")
    return Next("STEP_F1_CX")

@step
def STEP_F1_CX(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("wn", {}).get("f1_item"), path="0.center.x", default=0)
    cycle["wn"]["f1_cx"] = j.get("result")
    return Next("STEP_F1_CY")

@step
def STEP_F1_CY(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("wn", {}).get("f1_item"), path="0.center.y", default=0)
    cycle["wn"]["f1_cy"] = j.get("result")
    return Next("STEP_F1_CZ")

@step
def STEP_F1_CZ(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("wn", {}).get("f1_item"), path="0.center.z", default=0)
    cycle["wn"]["f1_cz"] = j.get("result")
    return Next("STEP_A1_CX")

@step
def STEP_A1_CX(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("wn", {}).get("a1_item"), path="0.center.x", default=0)
    cycle["wn"]["a1_cx"] = j.get("result")
    return Next("STEP_A1_CY")

@step
def STEP_A1_CY(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("wn", {}).get("a1_item"), path="0.center.y", default=0)
    cycle["wn"]["a1_cy"] = j.get("result")
    return Next("STEP_A1_CZ")

@step
def STEP_A1_CZ(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("wn", {}).get("a1_item"), path="0.center.z", default=0)
    cycle["wn"]["a1_cz"] = j.get("result")
    return Next("STEP_D1_CX")

@step
def STEP_D1_CX(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("wn", {}).get("d1_item"), path="0.center.x", default=0)
    cycle["wn"]["d1_cx"] = j.get("result")
    return Next("STEP_D1_CY")

@step
def STEP_D1_CY(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("wn", {}).get("d1_item"), path="0.center.y", default=0)
    cycle["wn"]["d1_cy"] = j.get("result")
    return Next("STEP_D1_CZ")

@step
def STEP_D1_CZ(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("wn", {}).get("d1_item"), path="0.center.z", default=0)
    cycle["wn"]["d1_cz"] = j.get("result")
    return Next("CC_EXIT_OK")

@step
def CC_EXIT_OK(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")
