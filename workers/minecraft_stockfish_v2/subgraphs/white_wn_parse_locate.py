

from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="WHITE_WN_PARSE_LOCATE",
    entry="STEP_PARSE",
    exits={"success": "WN_PL_DONE"}
)

@step
def STEP_PARSE(worker, cycle, env):
    uci = str(cycle.get("move", {}).get("uci") or "")
    out = env.transform("uci_parse", uci=uci)
    wn = cycle.setdefault("wn", {})
    wn["from"], wn["to"], wn["promo"] = out.get("from"), out.get("to"), out.get("promo")
    return Next("STEP_LOCATE_FROM")

@step
def STEP_LOCATE_FROM(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares,
                        predicate={"kind":"eq","path":"square","value":cycle.get("wn",{}).get("from")})
    cycle.setdefault("wn", {})["from_item"] = out.get("items") or []
    return Next("STEP_FROM_CX")

@step
def STEP_FROM_CX(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("wn",{}).get("from_item"), path="0.center.x", default=0)
    cycle["wn"]["from_cx"] = o.get("result")
    return Next("STEP_FROM_CY")

@step
def STEP_FROM_CY(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("wn",{}).get("from_item"), path="0.center.y", default=64)
    cycle["wn"]["from_cy"] = o.get("result")
    return Next("STEP_FROM_CZ")

@step
def STEP_FROM_CZ(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("wn",{}).get("from_item"), path="0.center.z", default=0)
    cycle["wn"]["from_cz"] = o.get("result")
    return Next("STEP_LOCATE_TO")

@step
def STEP_LOCATE_TO(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares,
                        predicate={"kind":"eq","path":"square","value":cycle.get("wn",{}).get("to")})
    cycle.setdefault("wn", {})["to_item"] = out.get("items") or []
    return Next("STEP_TO_CX")

@step
def STEP_TO_CX(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("wn",{}).get("to_item"), path="0.center.x", default=0)
    cycle["wn"]["to_cx"] = o.get("result")
    return Next("STEP_TO_CY")

@step
def STEP_TO_CY(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("wn",{}).get("to_item"), path="0.center.y", default=64)
    cycle["wn"]["to_cy"] = o.get("result")
    return Next("STEP_TO_CZ")

@step
def STEP_TO_CZ(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("wn",{}).get("to_item"), path="0.center.z", default=0)
    cycle["wn"]["to_cz"] = o.get("result")
    return Next("WN_PL_DONE")

@step
def WN_PL_DONE(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")
