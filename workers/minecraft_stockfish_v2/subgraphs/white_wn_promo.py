















from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="WHITE_WN_PROMO",
    entry="COND_PROMO",
    exits={"success": "WN_P_DONE"}
)

@cond
def COND_PROMO(worker, cycle, env):
    if cycle.get("wn", {}).get("promo"):
        return Next("STEP_PROMO_APPLY")
    return Exit("success")

@step
def STEP_PROMO_APPLY(worker, cycle, env):
    tx,ty,tz = cycle["wn"]["to_cx"], cycle["wn"]["to_cy"], cycle["wn"]["to_cz"]
    promo = str(cycle.get("wn", {}).get("promo") or "")
    cmd1 = ("execute positioned {tx} {ty} {tz} run data merge entity @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..0.9] "
            "{{CustomName:&\u0023;39;{\\\"text\\\":\\\"{promo}\\\"}&\u0023;39;,CustomNameVisible:1b}}" ).format(tx=tx,ty=ty,tz=tz,promo=promo)
    cmd2 = "tag @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..0.9] add promo_{promo}".format(promo=promo)
    env.tool("minecraft_control", operation="batch_commands", delay_ms=10, commands=[cmd1, cmd2])
    return Next("WN_P_DONE")

@step
def WN_P_DONE(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")
