

from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="ENGINE_B_EP_STRICT",
    entry="COND_AXIS",
    exits={"success": "EP_DONE"}
)

@cond
def COND_AXIS(worker, cycle, env):
    axis = str(worker.get("chess", {}).get("axis", "+x"))
    if axis == "+x":
        return Next("COND_WNO_POSX")
    if axis == "-x":
        return Next("COND_WNO_NEGX")
    if axis == "+z":
        return Next("COND_WNO_POSZ")
    return Next("COND_WNO_NEGZ")

@cond
def COND_WNO_POSX(worker, cycle, env):
    if bool(worker.get("chess", {}).get("white_near_origin", True)):
        return Next("STEP_EP_KILL_XM")
    return Next("STEP_EP_KILL_XP")

@cond
def COND_WNO_NEGX(worker, cycle, env):
    if bool(worker.get("chess", {}).get("white_near_origin", True)):
        return Next("STEP_EP_KILL_XP")
    return Next("STEP_EP_KILL_XM")

@cond
def COND_WNO_POSZ(worker, cycle, env):
    if bool(worker.get("chess", {}).get("white_near_origin", True)):
        return Next("STEP_EP_KILL_ZM")
    return Next("STEP_EP_KILL_ZP")

@cond
def COND_WNO_NEGZ(worker, cycle, env):
    if bool(worker.get("chess", {}).get("white_near_origin", True)):
        return Next("STEP_EP_KILL_ZP")
    return Next("STEP_EP_KILL_ZM")

@step
def STEP_EP_KILL_XP(worker, cycle, env):
    r = worker.get("engine", {}).get("anim", {}).get("target_capture_radius", 0.49)
    case = int(worker.get("chess", {}).get("case_size", 3))
    tx,ty,tz = cycle["eng"]["to_cx"], cycle["eng"]["to_cy"], cycle["eng"]["to_cz"]
    px = tx + case
    cmd = ("execute positioned {cx} {cy} {cz} run execute align xz positioned ~0.5 ~ ~0.5 "
           "unless entity @e[tag=chess_piece,tag=!chess_black_to_move,limit=1,sort=nearest,distance=..{r}] "
           "run execute positioned {px} {py} {pz} run execute align xz positioned ~0.5 ~ ~0.5 "
           "if entity @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{r}] run kill @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{r}]")
    env.tool("minecraft_control", operation="execute_command", command=cmd.format(cx=tx,cy=ty,cz=tz,px=px,py=ty,pz=tz,r=r))
    return Next("EP_DONE")

@step
def STEP_EP_KILL_XM(worker, cycle, env):
    r = worker.get("engine", {}).get("anim", {}).get("target_capture_radius", 0.49)
    case = int(worker.get("chess", {}).get("case_size", 3))
    tx,ty,tz = cycle["eng"]["to_cx"], cycle["eng"]["to_cy"], cycle["eng"]["to_cz"]
    px = tx - case
    cmd = ("execute positioned {cx} {cy} {cz} run execute align xz positioned ~0.5 ~ ~0.5 "
           "unless entity @e[tag=chess_piece,tag=!chess_black_to_move,limit=1,sort=nearest,distance=..{r}] "
           "run execute positioned {px} {py} {pz} run execute align xz positioned ~0.5 ~ ~0.5 "
           "if entity @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{r}] run kill @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{r}]")
    env.tool("minecraft_control", operation="execute_command", command=cmd.format(cx=tx,cy=ty,cz=tz,px=px,py=ty,pz=tz,r=r))
    return Next("EP_DONE")

@step
def STEP_EP_KILL_ZP(worker, cycle, env):
    r = worker.get("engine", {}).get("anim", {}).get("target_capture_radius", 0.49)
    case = int(worker.get("chess", {}).get("case_size", 3))
    tx,ty,tz = cycle["eng"]["to_cx"], cycle["eng"]["to_cy"], cycle["eng"]["to_cz"]
    pz = tz + case
    cmd = ("execute positioned {cx} {cy} {cz} run execute align xz positioned ~0.5 ~ ~0.5 "
           "unless entity @e[tag=chess_piece,tag=!chess_black_to_move,limit=1,sort=nearest,distance=..{r}] "
           "run execute positioned {px} {py} {pz} run execute align xz positioned ~0.5 ~ ~0.5 "
           "if entity @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{r}] run kill @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{r}]")
    env.tool("minecraft_control", operation="execute_command", command=cmd.format(cx=tx,cy=ty,cz=tz,px=tx,py=ty,pz=pz,r=r))
    return Next("EP_DONE")

@step
def STEP_EP_KILL_ZM(worker, cycle, env):
    r = worker.get("engine", {}).get("anim", {}).get("target_capture_radius", 0.49)
    case = int(worker.get("chess", {}).get("case_size", 3))
    tx,ty,tz = cycle["eng"]["to_cx"], cycle["eng"]["to_cy"], cycle["eng"]["to_cz"]
    pz = tz - case
    cmd = ("execute positioned {cx} {cy} {cz} run execute align xz positioned ~0.5 ~ ~0.5 "
           "unless entity @e[tag=chess_piece,tag=!chess_black_to_move,limit=1,sort=nearest,distance=..{r}] "
           "run execute positioned {px} {py} {pz} run execute align xz positioned ~0.5 ~ ~0.5 "
           "if entity @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{r}] run kill @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{r}]")
    env.tool("minecraft_control", operation="execute_command", command=cmd.format(cx=tx,cy=ty,cz=tz,px=tx,py=ty,pz=pz,r=r))
    return Next("EP_DONE")

@step
def EP_DONE(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")
