

from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="ENGINE_B_COMPUTE",
    entry="STEP_GET_MV",
    exits={"fail": "EC_EXIT_NOBEST", "success": "EC_EXIT_HASBEST"}
)

@step
def STEP_GET_MV(worker, cycle, env):
    mv = str(cycle.get("move", {}).get("uci") or "")
    out = env.transform("set_value", value=mv)
    cycle.setdefault("eng", {})["mv"] = out.get("result")
    return Next("STEP_GET_PREV")

@step
def STEP_GET_PREV(worker, cycle, env):
    prev = str((cycle.get("game") or {}).get("moves") or "")
    out = env.transform("set_value", value=prev)
    cycle.setdefault("eng", {})["prev"] = out.get("result")
    return Next("STEP_BUILD_MOVES")

@step
def STEP_BUILD_MOVES(worker, cycle, env):
    out = env.transform("format_template", template="{prev} {mv}", context={
        "prev": cycle.get("eng", {}).get("prev") or "",
        "mv": cycle.get("eng", {}).get("mv") or "",
    })
    cycle.setdefault("game", {})["moves"] = (out.get("result") or "").strip()
    return Next("STEP_EVAL")

@step
def STEP_EVAL(worker, cycle, env):
    nm = cycle.get("game", {}).get("moves")
    out = env.tool("stockfish_auto", operation="evaluate_position",
                   position={"startpos": True, "moves": nm},
                   quality=worker.get("stockfish", {}).get("quality"),
                   depth=int(worker.get("stockfish", {}).get("depth", 16)))
    cycle.setdefault("eng", {})["eval_raw"] = out
    return Next("STEP_PARSE_BEST")

@step
def STEP_PARSE_BEST(worker, cycle, env):
    out = env.transform("json_ops", op="get", data=cycle.get("eng", {}).get("eval_raw"), path="bestmove.move", default="")
    cycle.setdefault("eng", {})["best_uci"] = out.get("result")
    return Next("COND_HAS_BEST")

@cond
def COND_HAS_BEST(worker, cycle, env):
    if str(cycle.get("eng", {}).get("best_uci") or ""):
        return Exit("success")
    return Next("STEP_NO_BEST_MSG")

@step
def STEP_NO_BEST_MSG(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command",
             command="title @a[tag=chess_owner] actionbar {\\\"text\\\":\\\"Pas de coup noir (loop)\\\",\\\"color\\\":\\\"yellow\\\"}")
    return Exit("fail")
