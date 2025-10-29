from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="TURN_TIMER",
    entry="STEP_GET_NOW",
    exits={"success": "TT_EXIT_OK", "fail": "TT_EXIT_TIMEOUT"}
)

@step
def STEP_GET_NOW(worker, cycle, env):
    out = env.tool("date", operation="now", format="iso", timezone="UTC")
    cycle.setdefault("timer", {})["now"] = out.get("result")
    return Next("STEP_GET_LAST")

@step
def STEP_GET_LAST(worker, cycle, env):
    last = (cycle.get("game") or {}).get("last_turn_ts")
    out = env.transform("set_value", value=last)
    cycle.setdefault("timer", {})["last"] = out.get("result")
    return Next("COND_LAST_EXISTS")

@cond
def COND_LAST_EXISTS(worker, cycle, env):
    if cycle.get("timer", {}).get("last"):
        return Next("STEP_DIFF")
    return Next("STEP_STORE_START")

@step
def STEP_STORE_START(worker, cycle, env):
    out = env.transform("set_value", value=cycle.get("timer", {}).get("now"))
    cycle.setdefault("game", {})["last_turn_ts"] = out.get("result")
    # init elapsed to 0 on first store
    cycle.setdefault("timer", {})["elapsed_s"] = 0
    return Next("STEP_DIFF")

@step
def STEP_DIFF(worker, cycle, env):
    # Keep current accumulated elapsed_s (no date_ops.diff available). Must call exactly one transform.
    elapsed = float(cycle.get("timer", {}).get("elapsed_s") or 0)
    out = env.transform("set_value", value=elapsed)
    cycle.setdefault("timer", {})["elapsed_s"] = out.get("result")
    return Next("COND_TIMEOUT")

@cond
def COND_TIMEOUT(worker, cycle, env):
    elapsed = float(cycle.get("timer", {}).get("elapsed_s") or 0)
    if elapsed > float(worker.get("turns", {}).get("max_seconds", 120)):
        return Exit("fail")
    return Next("STEP_CHECK_LEVER")

@step
def STEP_CHECK_LEVER(worker, cycle, env):
    lv = cycle.get("lever", {})
    y = int(worker.get("chess", {}).get("y_level", 64)) + 1
    out = env.tool("minecraft_control", operation="execute_command",
                   command=f"execute if block {lv.get('x')} {y} {lv.get('z')} minecraft:lever[powered=true] run say [TURN] Interrupteur ON")
    cycle.setdefault("timer", {})["lever_check"] = out.get("result") or out.get("content") or ""
    return Next("COND_LEVER_ON")

@cond
def COND_LEVER_ON(worker, cycle, env):
    if "Interrupteur ON" in str(cycle.get("timer", {}).get("lever_check")):
        return Next("STEP_EQUIP_ON_CLICK")
    return Next("STEP_WAIT")

@step
def STEP_EQUIP_ON_CLICK(worker, cycle, env):
    cmds = [
        "say [TURN] Equipement du bâton",
        "item replace entity @a[tag=chess_owner] weapon.mainhand with minecraft:stick 1",
        "replaceitem entity @a[tag=chess_owner] weapon.mainhand minecraft:stick 1",
        "give @a[tag=chess_owner] minecraft:stick 1",
        "tag @a[tag=chess_owner] add chess_turn_active"
    ]
    env.tool("minecraft_control", operation="batch_commands", delay_ms=5, commands=cmds)
    cycle.setdefault("timer", {})["elapsed_s"] = 0
    return Exit("success")

@step
def STEP_WAIT(worker, cycle, env):
    ms = int(worker.get("turns", {}).get("lever_poll_ms", 5000))
    env.transform("sleep", ms=ms)
    prev = float(cycle.get("timer", {}).get("elapsed_s") or 0)
    cycle.setdefault("timer", {})["elapsed_s"] = prev + (ms / 1000.0)
    return Next("STEP_GET_NOW")
