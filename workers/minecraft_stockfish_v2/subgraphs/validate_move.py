from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="VALIDATE_MOVE",
    entry="STEP_EVAL_BEFORE",
    exits={"fail": "EXIT_BAD", "success": "EXIT_OK"}
)

@step
def STEP_EVAL_BEFORE(worker, cycle, env):
    pos = {"startpos": True, "moves": str((cycle.get("game") or {}).get("moves") or "")}
    out = env.tool("stockfish_auto", operation="evaluate_position",
                   position=pos, quality=worker.get("stockfish", {}).get("quality"),
                   limit=worker.get("stockfish", {}).get("limit"))
    cycle.setdefault("sf", {})["before"] = out
    return Next("STEP_EVAL_AFTER")

@step
def STEP_EVAL_AFTER(worker, cycle, env):
    moves = ((cycle.get("game") or {}).get("moves") or "") + " " + str(cycle.get("move", {}).get("uci") or "")
    out = env.tool("stockfish_auto", operation="evaluate_position",
                   position={"startpos": True, "moves": moves},
                   quality=worker.get("stockfish", {}).get("quality"),
                   limit=worker.get("stockfish", {}).get("limit"))
    cycle.setdefault("sf", {})["after"] = out
    return Next("STEP_GET_BTYPE")

@step
def STEP_GET_BTYPE(worker, cycle, env):
    btype = env.transform("json_ops", op="get", data=cycle.get("sf", {}).get("before"), path="result.lines.0.score.type", default="cp").get("result")
    cycle.setdefault("sf", {})["before_type"] = btype
    return Next("STEP_GET_ATYPE")

@step
def STEP_GET_ATYPE(worker, cycle, env):
    atype = env.transform("json_ops", op="get", data=cycle.get("sf", {}).get("after"), path="result.lines.0.score.type", default="cp").get("result")
    cycle.setdefault("sf", {})["after_type"] = atype
    return Next("STEP_GET_BVAL")

@step
def STEP_GET_BVAL(worker, cycle, env):
    bval = env.transform("json_ops", op="get", data=cycle.get("sf", {}).get("before"), path="result.lines.0.score.value", default=0).get("result")
    cycle.setdefault("sf", {})["before_val"] = bval
    return Next("STEP_GET_AVAL")

@step
def STEP_GET_AVAL(worker, cycle, env):
    aval = env.transform("json_ops", op="get", data=cycle.get("sf", {}).get("after"), path="result.lines.0.score.value", default=0).get("result")
    cycle.setdefault("sf", {})["after_val"] = aval
    return Next("STEP_COERCE_BEFORE")

@step
def STEP_COERCE_BEFORE(worker, cycle, env):
    out = env.transform("coerce_number", value=cycle.get("sf", {}).get("before_val"))
    cycle.setdefault("sf", {})["before_num"] = out.get("number")
    return Next("STEP_COERCE_AFTER")

@step
def STEP_COERCE_AFTER(worker, cycle, env):
    out = env.transform("coerce_number", value=cycle.get("sf", {}).get("after_val"))
    cycle.setdefault("sf", {})["after_num"] = out.get("number")
    return Next("COND_MATE_BEFORE")

@cond
def COND_MATE_BEFORE(worker, cycle, env):
    if str(cycle.get("sf", {}).get("before_type") or "cp") == "mate":
        return Next("COND_BEFORE_SIGN_POS")
    return Next("COND_MATE_AFTER")

@cond
def COND_BEFORE_SIGN_POS(worker, cycle, env):
    b = float(cycle.get("sf", {}).get("before_num") or 0)
    if b >= 0:
        return Next("STEP_SET_BEFORE_INF_POS")
    return Next("STEP_SET_BEFORE_INF_NEG")

@step
def STEP_SET_BEFORE_INF_POS(worker, cycle, env):
    out = env.transform("set_value", value=10000.0)
    cycle.setdefault("sf", {})["before_num"] = out.get("result")
    return Next("COND_MATE_AFTER")

@step
def STEP_SET_BEFORE_INF_NEG(worker, cycle, env):
    out = env.transform("set_value", value=-10000.0)
    cycle.setdefault("sf", {})["before_num"] = out.get("result")
    return Next("COND_MATE_AFTER")

@cond
def COND_MATE_AFTER(worker, cycle, env):
    if str(cycle.get("sf", {}).get("after_type") or "cp") == "mate":
        return Next("COND_AFTER_SIGN_POS")
    return Next("STEP_DELTA")

@cond
def COND_AFTER_SIGN_POS(worker, cycle, env):
    a = float(cycle.get("sf", {}).get("after_num") or 0)
    if a >= 0:
        return Next("STEP_SET_AFTER_INF_POS")
    return Next("STEP_SET_AFTER_INF_NEG")

@step
def STEP_SET_AFTER_INF_POS(worker, cycle, env):
    out = env.transform("set_value", value=10000.0)
    cycle.setdefault("sf", {})["after_num"] = out.get("result")
    return Next("STEP_DELTA")

@step
def STEP_SET_AFTER_INF_NEG(worker, cycle, env):
    out = env.transform("set_value", value=-10000.0)
    cycle.setdefault("sf", {})["after_num"] = out.get("result")
    return Next("STEP_DELTA")

@step
def STEP_DELTA(worker, cycle, env):
    out = env.transform("arithmetic", op="sub", a=cycle.get("sf", {}).get("after_num"), b=cycle.get("sf", {}).get("before_num"))
    cycle.setdefault("sf", {})["delta_cp"] = out.get("result")
    return Next("COND_BAD")

@cond
def COND_BAD(worker, cycle, env):
    delta = float(cycle.get("sf", {}).get("delta_cp") or 0)
    thr = float(worker.get("turns", {}).get("bad_move_threshold_cp", -300))
    if delta < thr:
        return Exit("fail")
    return Exit("success")
