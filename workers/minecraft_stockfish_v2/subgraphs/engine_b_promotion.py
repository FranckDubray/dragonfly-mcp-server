












from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="ENGINE_B_PROMOTION",
    entry="STEP_PROMO_CHECK",
    exits={"success": "PR_EXIT"}
)

@step
def STEP_PROMO_CHECK(worker, cycle, env):
    promo = str(cycle.get("eng", {}).get("promo") or "")
    out = env.transform("set_value", value=promo)
    cycle.setdefault("eng", {})["promo_val"] = out.get("result")
    return Next("COND_PROMO")

@cond
def COND_PROMO(worker, cycle, env):
    if str(cycle.get("eng", {}).get("promo_val") or ""):
        return Next("STEP_PROMO_JSON")
    return Exit("success")

@step
def STEP_PROMO_JSON(worker, cycle, env):
    promo = str(cycle.get("eng", {}).get("promo_val") or "")
    out = env.transform("format_template", template='{"text":"{{promo}}"}', context={"promo": promo})
    cycle.setdefault("eng", {})["promo_inner_json"] = out.get("result")
    return Next("STEP_PROMO_APPLY")

@step
def STEP_PROMO_APPLY(worker, cycle, env):
    inner = cycle.get("eng", {}).get("promo_inner_json")
    tx,ty,tz = cycle["eng"]["to_cx"], cycle["eng"]["to_cy"], cycle["eng"]["to_cz"]
    cmd = (
        f"execute positioned {tx} {ty} {tz} run "
        f"data merge entity @e[tag=chess_black_to_move,limit=1,sort=nearest] "
        f"{{CustomName:'{inner}',CustomNameVisible:1b}}"
    )
    env.tool("minecraft_control", operation="execute_command", command=cmd)
    return Next("STEP_PROMO_TAG")

@step
def STEP_PROMO_TAG(worker, cycle, env):
    promo = str(cycle.get("eng", {}).get("promo_val") or "")
    env.tool("minecraft_control", operation="execute_command", command=f"tag @e[tag=chess_black_to_move,limit=1,sort=nearest] add promo_{promo}")
    return Exit("success")

 
 
 
 
 
 
 
 
 
 
 
