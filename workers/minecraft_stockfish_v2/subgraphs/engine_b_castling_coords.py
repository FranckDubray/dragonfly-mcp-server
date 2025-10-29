



























from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="ENGINE_B_CASTLING_COORDS",
    entry="ENG_CC_FETCH_SQUARES",
    exits={"success": "CC_EXIT_OK"}
)

@step
def ENG_CC_FETCH_SQUARES(worker, cycle, env):
    # Keep a local copy of squares to minimize repeated lookups
    out = env.transform("set_value", value=cycle.get("mc", {}).get("board", {}).get("squares", []))
    cycle.setdefault("eng", {})["_squares"] = out.get("result") or []
    return Next("STEP_FILTER_A8_H8_F8_D8")

@step
def STEP_FILTER_A8_H8_F8_D8(worker, cycle, env):
    squares = cycle.get("eng", {}).get("_squares", [])
    # Small helper map so we can reuse the same list for each filter
    out = env.transform("set_value", value={"a8": squares, "h8": squares, "f8": squares, "d8": squares})
    cycle.setdefault("eng", {})["_sq_map"] = out.get("result")
    return Next("STEP_GET_A8")

@step
def STEP_GET_A8(worker, cycle, env):
    squares = cycle.get("eng", {}).get("_sq_map", {}).get("a8", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"a8"})
    cycle.setdefault("eng", {})["a8_item"] = out.get("items") or []
    return Next("STEP_GET_H8")

@step
def STEP_GET_H8(worker, cycle, env):
    squares = cycle.get("eng", {}).get("_sq_map", {}).get("h8", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"h8"})
    cycle.setdefault("eng", {})["h8_item"] = out.get("items") or []
    return Next("STEP_GET_F8")

@step
def STEP_GET_F8(worker, cycle, env):
    squares = cycle.get("eng", {}).get("_sq_map", {}).get("f8", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"f8"})
    cycle.setdefault("eng", {})["f8_item"] = out.get("items") or []
    return Next("STEP_GET_D8")

@step
def STEP_GET_D8(worker, cycle, env):
    squares = cycle.get("eng", {}).get("_sq_map", {}).get("d8", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"d8"})
    cycle.setdefault("eng", {})["d8_item"] = out.get("items") or []
    return Next("STEP_H8_CX")

@step
def STEP_H8_CX(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("eng", {}).get("h8_item"), path="0.center.x", default=0)
    cycle["eng"]["h8_cx"] = j.get("result")
    return Next("STEP_H8_CY")

@step
def STEP_H8_CY(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("eng", {}).get("h8_item"), path="0.center.y", default=0)
    cycle["eng"]["h8_cy"] = j.get("result")
    return Next("STEP_H8_CZ")

@step
def STEP_H8_CZ(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("eng", {}).get("h8_item"), path="0.center.z", default=0)
    cycle["eng"]["h8_cz"] = j.get("result")
    return Next("STEP_F8_CX")

@step
def STEP_F8_CX(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("eng", {}).get("f8_item"), path="0.center.x", default=0)
    cycle["eng"]["f8_cx"] = j.get("result")
    return Next("STEP_F8_CY")

@step
def STEP_F8_CY(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("eng", {}).get("f8_item"), path="0.center.y", default=0)
    cycle["eng"]["f8_cy"] = j.get("result")
    return Next("STEP_F8_CZ")

@step
def STEP_F8_CZ(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("eng", {}).get("f8_item"), path="0.center.z", default=0)
    cycle["eng"]["f8_cz"] = j.get("result")
    return Next("STEP_A8_CX")

@step
def STEP_A8_CX(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("eng", {}).get("a8_item"), path="0.center.x", default=0)
    cycle["eng"]["a8_cx"] = j.get("result")
    return Next("STEP_A8_CY")

@step
def STEP_A8_CY(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("eng", {}).get("a8_item"), path="0.center.y", default=0)
    cycle["eng"]["a8_cy"] = j.get("result")
    return Next("STEP_A8_CZ")

@step
def STEP_A8_CZ(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("eng", {}).get("a8_item"), path="0.center.z", default=0)
    cycle["eng"]["a8_cz"] = j.get("result")
    return Next("STEP_D8_CX")

@step
def STEP_D8_CX(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("eng", {}).get("d8_item"), path="0.center.x", default=0)
    cycle["eng"]["d8_cx"] = j.get("result")
    return Next("STEP_D8_CY")

@step
def STEP_D8_CY(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("eng", {}).get("d8_item"), path="0.center.y", default=0)
    cycle["eng"]["d8_cy"] = j.get("result")
    return Next("STEP_D8_CZ")

@step
def STEP_D8_CZ(worker, cycle, env):
    j = env.transform("json_ops", op="get", data=cycle.get("eng", {}).get("d8_item"), path="0.center.z", default=0)
    cycle["eng"]["d8_cz"] = j.get("result")
    return Next("CC_EXIT_OK")

@step
def CC_EXIT_OK(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 