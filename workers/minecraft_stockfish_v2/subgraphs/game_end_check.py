















from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="GAME_END_CHECK",
    entry="STEP_GET_MVW",
    exits={"success": "GE_CONTINUE"}
)

@step
def STEP_GET_MVW(worker, cycle, env):
    # Capture current white moves (do not modify game.moves here)
    mvw = str((cycle.get("game") or {}).get("moves") or "").strip()
    out = env.transform("set_value", value=mvw)
    cycle.setdefault("endchk", {})["mvw"] = out.get("result")
    return Next("STEP_GET_BMV")

@step
def STEP_GET_BMV(worker, cycle, env):
    bmv = str((cycle.get("eng") or {}).get("best_uci") or "").strip()
    out = env.transform("set_value", value=bmv)
    cycle.setdefault("endchk", {})["bmv"] = out.get("result")
    return Next("COND_HAS_BMV")

@cond
def COND_HAS_BMV(worker, cycle, env):
    bmv = str(cycle.get("endchk", {}).get("bmv") or "")
    if bmv:
        return Next("STEP_BUILD_TMP")
    # No best move for Black → evaluate after White only to detect win/stalemate
    return Next("STEP_EVAL_AFTER_WHITE")

@step
def STEP_EVAL_AFTER_WHITE(worker, cycle, env):
    mvw = str(cycle.get("endchk", {}).get("mvw") or "")
    out = env.tool(
        "stockfish_auto", operation="evaluate_position",
        position={"startpos": True, "moves": mvw},
        quality=worker.get("stockfish", {}).get("quality"),
        limit=worker.get("stockfish", {}).get("limit")
    )
    cycle.setdefault("endchk", {})["eval_aw"] = out
    return Next("STEP_GET_STYPE_AW")

@step
def STEP_GET_STYPE_AW(worker, cycle, env):
    ev = cycle.get("endchk", {}).get("eval_aw")
    stype = env.transform("json_ops", op="get", data=ev, path="result.lines.0.score.type", default="cp").get("result")
    cycle.setdefault("endchk", {})["score_type_aw"] = stype
    return Next("COND_WIN_OR_DRAW")

@cond
def COND_WIN_OR_DRAW(worker, cycle, env):
    stype = str(cycle.get("endchk", {}).get("score_type_aw") or "cp")
    if stype == "mate":
        cycle.setdefault("endchk", {})["status"] = "win"
    else:
        cycle.setdefault("endchk", {})["status"] = "continue"
    return Next("GE_CONTINUE")

@step
def STEP_BUILD_TMP(worker, cycle, env):
    mvw = str(cycle.get("endchk", {}).get("mvw") or "")
    bmv = str(cycle.get("endchk", {}).get("bmv") or "")
    tmp = (mvw + " " + bmv).strip()
    out = env.transform("set_value", value=tmp)
    cycle.setdefault("endchk", {})["temp_moves"] = out.get("result")
    return Next("STEP_EVAL")

@step
def STEP_EVAL(worker, cycle, env):
    tmp = cycle.get("endchk", {}).get("temp_moves") or ""
    out = env.tool(
        "stockfish_auto", operation="evaluate_position",
        position={"startpos": True, "moves": tmp},
        quality=worker.get("stockfish", {}).get("quality"),
        limit=worker.get("stockfish", {}).get("limit")
    )
    cycle.setdefault("endchk", {})["eval"] = out
    return Next("STEP_GET_BEST_RAW")

@step
def STEP_GET_BEST_RAW(worker, cycle, env):
    ev = cycle.get("endchk", {}).get("eval")
    best = env.transform("json_ops", op="get", data=ev, path="bestmove.move", default="").get("result")
    cycle.setdefault("endchk", {})["best_raw"] = best
    return Next("STEP_SET_BEST")

@step
def STEP_SET_BEST(worker, cycle, env):
    b = cycle.get("endchk", {}).get("best_raw")
    out = env.transform("set_value", value=str(b or ""))
    cycle.setdefault("endchk", {})["best_after_black"] = out.get("result")
    return Next("STEP_GET_STYPE")

@step
def STEP_GET_STYPE(worker, cycle, env):
    ev = cycle.get("endchk", {}).get("eval")
    stype = env.transform("json_ops", op="get", data=ev, path="result.lines.0.score.type", default="cp").get("result")
    cycle.setdefault("endchk", {})["score_type"] = stype
    return Next("STEP_GET_SVAL")

@step
def STEP_GET_SVAL(worker, cycle, env):
    ev = cycle.get("endchk", {}).get("eval")
    sval = env.transform("json_ops", op="get", data=ev, path="result.lines.0.score.value", default=0).get("result")
    cycle.setdefault("endchk", {})["score_val"] = sval
    return Next("COND_NO_LEGAL")

@cond
def COND_NO_LEGAL(worker, cycle, env):
    # If no legal move for White after Black's move, it's either checkmate or stalemate.
    best = str(cycle.get("endchk", {}).get("best_after_black") or "")
    if not best:
        return Next("COND_IS_MATE")
    return Next("GE_CONTINUE")

@cond
def COND_IS_MATE(worker, cycle, env):
    # If score type is 'mate', side to move (White) is in check → checkmate → player lost.
    stype = str(cycle.get("endchk", {}).get("score_type") or "cp")
    if stype == "mate":
        cycle.setdefault("endchk", {})["status"] = "lost"
        return Next("GE_CONTINUE")
    # No legal moves but not 'mate' → stalemate: continue (no TNT)
    cycle.setdefault("endchk", {})["status"] = "continue"
    return Next("GE_CONTINUE")

@step
def GE_CONTINUE(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")

 
 
 
 
 
 
 
