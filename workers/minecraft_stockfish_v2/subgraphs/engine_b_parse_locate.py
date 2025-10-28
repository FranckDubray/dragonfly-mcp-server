


from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="ENGINE_B_PARSE_LOCATE",
    entry="STEP_PARSE",
    exits={"success": "PL_DONE"}
)

@step
def STEP_PARSE(worker, cycle, env):
    best = str(cycle.get("eng", {}).get("best_uci") or "")
    p = env.transform("uci_parse", uci=best)
    cycle.setdefault("eng", {}).update({"from": p.get("from"), "to": p.get("to"), "promo": p.get("promo")})
    return Next("STEP_FIND_FROM")

@step
def STEP_FIND_FROM(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":cycle.get("eng",{}).get("from")})
    cycle.setdefault("eng", {})["from_item"] = out.get("items") or []
    return Next("STEP_FROM_CX")

@step
def STEP_FROM_CX(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("from_item"), path="0.center.x", default=0)
    cycle["eng"]["from_cx"] = o.get("result")
    return Next("STEP_FROM_CY")

@step
def STEP_FROM_CY(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("from_item"), path="0.center.y", default=64)
    cycle["eng"]["from_cy"] = o.get("result")
    return Next("STEP_FROM_CZ")

@step
def STEP_FROM_CZ(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("from_item"), path="0.center.z", default=0)
    cycle["eng"]["from_cz"] = o.get("result")
    return Next("STEP_FIND_TO")

@step
def STEP_FIND_TO(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":cycle.get("eng",{}).get("to")})
    cycle.setdefault("eng", {})["to_item"] = out.get("items") or []
    return Next("STEP_TO_CX")

@step
def STEP_TO_CX(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("to_item"), path="0.center.x", default=0)
    cycle["eng"]["to_cx"] = o.get("result")
    return Next("STEP_TO_CY")

@step
def STEP_TO_CY(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("to_item"), path="0.center.y", default=64)
    cycle["eng"]["to_cy"] = o.get("result")
    return Next("STEP_TO_CZ")

@step
def STEP_TO_CZ(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("to_item"), path="0.center.z", default=0)
    cycle["eng"]["to_cz"] = o.get("result")
    return Next("PL_DONE")

@step
def PL_DONE(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")
