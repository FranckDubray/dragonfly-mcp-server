
















from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="MOVE_PIPELINE",
    entry="STEP_GET_NOW",
    exits={"fail": "EXIT_TIMEOUT", "success": "EXIT_MOVED"}
)

@step
def STEP_GET_NOW(worker, cycle, env):
    out = env.tool("date", operation="now", format="iso", timezone="UTC")
    cycle.setdefault("timer", {})["now"] = out.get("result")
    return Next("STEP_DIFF_FROM_LAST")

@step
def STEP_DIFF_FROM_LAST(worker, cycle, env):
    now = cycle.get("timer", {}).get("now")
    last = (cycle.get("game") or {}).get("last_turn_ts")
    out = env.transform("date_ops", ops=[{"op":"diff","a":now,"b":last,"unit":"seconds","save_as":"elapsed"}])
    cycle.setdefault("timer", {})["elapsed_s"] = out.get("elapsed")
    return Next("COND_TIMEOUT")

@cond
def COND_TIMEOUT(worker, cycle, env):
    if float(cycle.get("timer", {}).get("elapsed_s") or 0) > float(worker.get("turns", {}).get("max_seconds", 120)):
        return Exit("fail")
    return Next("STEP_LIST_ENTS")

@step
def STEP_LIST_ENTS(worker, cycle, env):
    p = cycle.get("plat", {})
    y = int(worker.get("chess", {}).get("y_level", 64))
    out = env.tool("minecraft_control", operation="list_entities", selector="@e[tag=chess_piece]",
                   area={"mode":"aabb","aabb":{"min":{"x":p.get("x1"),"y":y+worker['chess']['scan_y_min_offset'],"z":p.get("z1")},
                                              "max":{"x":p.get("x2"),"y":y+worker['chess']['scan_y_max_offset'],"z":p.get("z2")}}},
                   fields=["uuid","custom_name","pos","tags"], limit=64)
    cycle.setdefault("mc", {})["raw"] = out.get("result") or out.get("items") or []
    return Next("STEP_NORM")

@step
def STEP_NORM(worker, cycle, env):
    out = env.transform("normalize_entities", items=cycle.get("mc", {}).get("raw"))
    cycle.setdefault("mc", {})["norm"] = out.get("items") or []
    return Next("STEP_SORT")

@step
def STEP_SORT(worker, cycle, env):
    out = env.transform("array_ops", op="sort_by", items=cycle.get("mc", {}).get("norm", []), key="pos.y", order="desc")
    cycle["mc"]["sorted"] = out.get("items") or []
    return Next("STEP_UNIQ")

@step
def STEP_UNIQ(worker, cycle, env):
    out = env.transform("array_ops", op="unique_by", items=cycle.get("mc", {}).get("sorted", []), key="piece_key")
    cycle["mc"]["dedup"] = out.get("items") or []
    return Next("STEP_SNAP")

@step
def STEP_SNAP(worker, cycle, env):
    out = env.transform("pos_to_square", items=cycle.get("mc", {}).get("dedup", []),
                        origin=worker.get("chess", {}).get("origin_center"),
                        axis=worker.get("chess", {}).get("axis"),
                        case_size=worker.get("chess", {}).get("case_size"),
                        epsilon=worker.get("chess", {}).get("epsilon_snap", 0.8))
    cycle.setdefault("curr", {})["positions"] = out.get("map") or {}
    return Next("STEP_COMPARE")

@step
def STEP_COMPARE(worker, cycle, env):
    out = env.transform("compare_positions", prev=cycle.get("prev", {}).get("positions", {}), curr=cycle.get("curr", {}).get("positions", {}))
    cycle.setdefault("move", {})["unique"] = out.get("unique")
    cycle["move"]["piece_key"] = out.get("piece_key")
    cycle["move"]["from"] = out.get("from")
    cycle["move"]["to"] = out.get("to")
    return Next("COND_UNIQUE")

@cond
def COND_UNIQUE(worker, cycle, env):
    if cycle.get("move", {}).get("unique"):
        return Next("STEP_SET_PREV")
    return Next("STEP_WAIT")

@step
def STEP_SET_PREV(worker, cycle, env):
    out = env.transform("set_value", value=cycle.get("curr", {}).get("positions"))
    cycle.setdefault("prev", {})["positions"] = out.get("result")
    return Next("STEP_BUILD_UCI")

@step
def STEP_BUILD_UCI(worker, cycle, env):
    out = env.transform("uci_build", _from=cycle.get("move", {}).get("from"), to=cycle.get("move", {}).get("to"))
    cycle["move"]["uci"] = out.get("uci")
    return Exit("success")

@step
def STEP_WAIT(worker, cycle, env):
    env.transform("sleep", ms=int(worker.get("turns", {}).get("move_poll_ms", 5000)))
    return Next("STEP_GET_NOW")

 
 
 
 
 
 
 
 
 
 
 
