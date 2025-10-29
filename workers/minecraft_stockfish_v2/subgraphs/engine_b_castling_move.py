



























from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="ENGINE_B_CASTLING_MOVE",
    entry="ENG_CM_SIDE",
    exits={"success": "CM_DONE"}
)

@cond
def ENG_CM_SIDE(worker, cycle, env):
    side = str(cycle.get("eng", {}).get("_castle_side") or "").lower()
    if side == "ks":
        return Next("KS_CAPTURE_F8")
    if side == "qs":
        return Next("QS_CAPTURE_D8")
    # No castling: nothing to move
    return Next("CM_DONE")

@step
def KS_CAPTURE_F8(worker, cycle, env):
    r = worker.get("engine", {}).get("anim", {}).get("target_capture_radius", 0.49)
    x,y,z = cycle["eng"].get("f8_cx"), cycle["eng"].get("f8_cy"), cycle["eng"].get("f8_cz")
    env.tool("minecraft_control", operation="execute_command",
             command=(f"execute positioned {x} {y} {z} run execute align xz positioned ~0.5 ~ ~0.5 "
                      f"if entity @e[tag=chess_piece,tag=!chess_black_to_move,distance=..{r},limit=1,sort=nearest] "
                      f"run kill @e[tag=chess_piece,tag=!chess_black_to_move,distance=..{r},limit=1,sort=nearest]"))
    return Next("KS_TP_H8_TO_F8_LIFT")

@step
def KS_TP_H8_TO_F8_LIFT(worker, cycle, env):
    h = worker.get("engine", {}).get("anim", {}).get("lift_height", 1.2)
    hx,hy,hz = cycle["eng"].get("h8_cx"), cycle["eng"].get("h8_cy"), cycle["eng"].get("h8_cz")
    fx,fy,fz = cycle["eng"].get("f8_cx"), cycle["eng"].get("f8_cy"), cycle["eng"].get("f8_cz")
    env.tool("minecraft_control", operation="execute_command",
             command=(f"execute positioned {hx} {hy} {hz} run execute align xz positioned ~0.5 ~{h} ~0.5 "
                      f"run tp @e[tag=chess_piece,tag=b,limit=1,sort=nearest,distance=..0.9] {fx} {fy} {fz}"))
    return Next("KS_TP_H8_TO_F8_SNAP")

@step
def KS_TP_H8_TO_F8_SNAP(worker, cycle, env):
    fx,fy,fz = cycle["eng"].get("f8_cx"), cycle["eng"].get("f8_cy"), cycle["eng"].get("f8_cz")
    env.tool("minecraft_control", operation="execute_command",
             command=(f"execute positioned {fx} {fy} {fz} run execute align xz positioned ~0.5 ~ ~0.5 run tp @e[tag=chess_piece,tag=b,limit=1,sort=nearest] ~ ~ ~"))
    return Next("CM_DONE")

@step
def QS_CAPTURE_D8(worker, cycle, env):
    r = worker.get("engine", {}).get("anim", {}).get("target_capture_radius", 0.49)
    x,y,z = cycle["eng"].get("d8_cx"), cycle["eng"].get("d8_cy"), cycle["eng"].get("d8_cz")
    env.tool("minecraft_control", operation="execute_command",
             command=(f"execute positioned {x} {y} {z} run execute align xz positioned ~0.5 ~ ~0.5 "
                      f"if entity @e[tag=chess_piece,tag=!chess_black_to_move,distance=..{r},limit=1,sort=nearest] "
                      f"run kill @e[tag=chess_piece,tag=!chess_black_to_move,distance=..{r},limit=1,sort=nearest]"))
    return Next("QS_TP_A8_TO_D8_LIFT")

@step
def QS_TP_A8_TO_D8_LIFT(worker, cycle, env):
    h = worker.get("engine", {}).get("anim", {}).get("lift_height", 1.2)
    ax,ay,az = cycle["eng"].get("a8_cx"), cycle["eng"].get("a8_cy"), cycle["eng"].get("a8_cz")
    dx,dy,dz = cycle["eng"].get("d8_cx"), cycle["eng"].get("d8_cy"), cycle["eng"].get("d8_cz")
    env.tool("minecraft_control", operation="execute_command",
             command=(f"execute positioned {ax} {ay} {az} run execute align xz positioned ~0.5 ~{h} ~0.5 "
                      f"run tp @e[tag=chess_piece,tag=b,limit=1,sort=nearest,distance=..0.9] {dx} {dy} {dz}"))
    return Next("QS_TP_A8_TO_D8_SNAP")

@step
def QS_TP_A8_TO_D8_SNAP(worker, cycle, env):
    dx,dy,dz = cycle["eng"].get("d8_cx"), cycle["eng"].get("d8_cy"), cycle["eng"].get("d8_cz")
    env.tool("minecraft_control", operation="execute_command",
             command=(f"execute positioned {dx} {dy} {dz} run execute align xz positioned ~0.5 ~ ~0.5 run tp @e[tag=chess_piece,tag=b,limit=1,sort=nearest] ~ ~ ~"))
    return Next("CM_DONE")

@step
def CM_DONE(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
