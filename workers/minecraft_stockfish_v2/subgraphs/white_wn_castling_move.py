



























from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="WHITE_WN_CASTLING_MOVE",
    entry="WN_CM_SIDE",
    exits={"success": "CM_DONE"}
)

@cond
def WN_CM_SIDE(worker, cycle, env):
    side = str(cycle.get("wn", {}).get("_castle_side") or "").lower()
    if side == "ks":
        return Next("KS_CAPTURE_F1")
    if side == "qs":
        return Next("QS_CAPTURE_D1")
    return Exit("success")

@step
def KS_CAPTURE_F1(worker, cycle, env):
    x,y,z = cycle["wn"].get("f1_cx"), cycle["wn"].get("f1_cy"), cycle["wn"].get("f1_cz")
    env.tool("minecraft_control", operation="execute_command",
             command=f"execute positioned {x} {y} {z} run execute align xz positioned ~0.5 ~ ~0.5 if entity @e[tag=chess_piece,tag=w,distance=..0.49,limit=1,sort=nearest] run kill @e[tag=chess_piece,tag=w,distance=..0.49,limit=1,sort=nearest]")
    return Next("KS_TP_H1_TO_F1")

@step
def KS_TP_H1_TO_F1(worker, cycle, env):
    hx,hy,hz = cycle["wn"].get("h1_cx"), cycle["wn"].get("h1_cy"), cycle["wn"].get("h1_cz")
    fx,fy,fz = cycle["wn"].get("f1_cx"), cycle["wn"].get("f1_cy"), cycle["wn"].get("f1_cz")
    env.tool("minecraft_control", operation="execute_command",
             command=f"execute positioned {hx} {hy} {hz} run execute align xz positioned ~0.5 ~1.2 ~0.5 run tp @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..0.9] {fx} {fy} {fz}")
    return Next("KS_SNAP_F1")

@step
def KS_SNAP_F1(worker, cycle, env):
    x,y,z = cycle["wn"].get("f1_cx"), cycle["wn"].get("f1_cy"), cycle["wn"].get("f1_cz")
    env.tool("minecraft_control", operation="execute_command",
             command=f"execute positioned {x} {y} {z} run execute align xz positioned ~0.5 ~ ~0.5 run tp @e[tag=chess_piece,tag=w,limit=1,sort=nearest] ~ ~ ~")
    return Next("CM_DONE")

@step
def QS_CAPTURE_D1(worker, cycle, env):
    x,y,z = cycle["wn"].get("d1_cx"), cycle["wn"].get("d1_cy"), cycle["wn"].get("d1_cz")
    env.tool("minecraft_control", operation="execute_command",
             command=f"execute positioned {x} {y} {z} run execute align xz positioned ~0.5 ~ ~0.5 if entity @e[tag=chess_piece,tag=w,distance=..0.49,limit=1,sort=nearest] run kill @e[tag=chess_piece,tag=w,distance=..0.49,limit=1,sort=nearest]")
    return Next("QS_TP_A1_TO_D1")

@step
def QS_TP_A1_TO_D1(worker, cycle, env):
    ax,ay,az = cycle["wn"].get("a1_cx"), cycle["wn"].get("a1_cy"), cycle["wn"].get("a1_cz")
    dx,dy,dz = cycle["wn"].get("d1_cx"), cycle["wn"].get("d1_cy"), cycle["wn"].get("d1_cz")
    env.tool("minecraft_control", operation="execute_command",
             command=f"execute positioned {ax} {ay} {az} run execute align xz positioned ~0.5 ~1.2 ~0.5 run tp @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..0.9] {dx} {dy} {dz}")
    return Next("QS_SNAP_D1")

@step
def QS_SNAP_D1(worker, cycle, env):
    x,y,z = cycle["wn"].get("d1_cx"), cycle["wn"].get("d1_cy"), cycle["wn"].get("d1_cz")
    env.tool("minecraft_control", operation="execute_command",
             command=f"execute positioned {x} {y} {z} run execute align xz positioned ~0.5 ~ ~0.5 run tp @e[tag=chess_piece,tag=w,limit=1,sort=nearest] ~ ~ ~")
    return Next("CM_DONE")

@step
def CM_DONE(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 