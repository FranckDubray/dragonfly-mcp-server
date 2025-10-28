

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
    return Next("STEP_DIFF")

@step
def STEP_DIFF(worker, cycle, env):
    out = env.transform("date_ops", ops=[{"op":"diff","a":cycle["timer"]["now"],"b":cycle["game"]["last_turn_ts"],"unit":"seconds","save_as":"elapsed"}])
    cycle["timer"]["elapsed_s"] = out.get("elapsed")
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
                   command=f"execute if block {lv.get('x')} {y} {lv.get('z')} minecraft:lever[powered=true] run say LEVER_ON")
    cycle.setdefault("timer", {})["lever_check"] = out.get("result") or out.get("content") or ""
    return Next("COND_LEVER_ON")

@cond
def COND_LEVER_ON(worker, cycle, env):
    if "LEVER_ON" in str(cycle.get("timer", {}).get("lever_check")):
        return Exit("success")
    return Next("STEP_WAIT")

@step
def STEP_WAIT(worker, cycle, env):
    env.transform("sleep", ms=int(worker.get("turns", {}).get("lever_poll_ms", 5000)))
    return Next("STEP_GET_NOW")
