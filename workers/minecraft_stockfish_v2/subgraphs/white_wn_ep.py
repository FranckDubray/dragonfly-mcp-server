

from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="WHITE_WN_EP",
    entry="COND_EP_AXIS",
    exits={"success": "WN_EP_DONE"}
)

@cond
def COND_EP_AXIS(worker, cycle, env):
    axis = str(worker.get("chess", {}).get("axis", "+x"))
    if axis == "+x":
        return Next("COND_EP_WNO_POSX")
    if axis == "-x":
        return Next("COND_EP_WNO_NEGX")
    if axis == "+z":
        return Next("COND_EP_WNO_POSZ")
    return Next("COND_EP_WNO_NEGZ")

@cond
def COND_EP_WNO_POSX(worker, cycle, env):
    if bool(worker.get("chess", {}).get("white_near_origin", True)):
        return Next("STEP_EP_XM")
    return Next("STEP_EP_XP")

@cond
def COND_EP_WNO_NEGX(worker, cycle, env):
    if bool(worker.get("chess", {}).get("white_near_origin", True)):
        return Next("STEP_EP_XP")
    return Next("STEP_EP_XM")

@cond
def COND_EP_WNO_POSZ(worker, cycle, env):
    if bool(worker.get("chess", {}).get("white_near_origin", True)):
        return Next("STEP_EP_ZM")
    return Next("STEP_EP_ZP")

@cond
def COND_EP_WNO_NEGZ(worker, cycle, env):
    if bool(worker.get("chess", {}).get("white_near_origin", True)):
        return Next("STEP_EP_ZP")
    return Next("STEP_EP_ZM")

@step
def STEP_EP_XP(worker, cycle, env):
    tx,ty,tz = cycle["wn"]["to_cx"], cycle["wn"]["to_cy"], cycle["wn"]["to_cz"]
    case = int(worker.get("chess", {}).get("case_size", 3))
    px = tx + case
    cmd = ("execute positioned {cx} {cy} {cz} run execute align xz positioned ~0.5 ~ ~0.5 "
           "unless entity @e[tag=chess_piece,distance=..0.49,limit=1] run execute positioned {px} {py} {pz} "
           "run execute align xz positioned ~0.5 ~ ~0.5 if entity @e[tag=chess_piece,tag=b,limit=1,sort=nearest,distance=..0.49] run kill @e[tag=chess_piece,tag=b,limit=1,sort=nearest,distance=..0.49]")
    env.tool("minecraft_control", operation="execute_command", command=cmd.format(cx=tx,cy=ty,cz=tz,px=px,py=ty,pz=tz))
    return Next("WN_EP_DONE")

@step
def STEP_EP_XM(worker, cycle, env):
    tx,ty,tz = cycle["wn"]["to_cx"], cycle["wn"]["to_cy"], cycle["wn"]["to_cz"]
    case = int(worker.get("chess", {}).get("case_size", 3))
    px = tx - case
    cmd = ("execute positioned {cx} {cy} {cz} run execute align xz positioned ~0.5 ~ ~0.5 "
           "unless entity @e[tag=chess_piece,distance=..0.49,limit=1] run execute positioned {px} {py} {pz} "
           "run execute align xz positioned ~0.5 ~ ~0.5 if entity @e[tag=chess_piece,tag=b,limit=1,sort=nearest,distance=..0.49] run kill @e[tag=chess_piece,tag=b,limit=1,sort=nearest,distance=..0.49]")
    env.tool("minecraft_control", operation="execute_command", command=cmd.format(cx=tx,cy=ty,cz=tz,px=px,py=ty,pz=tz))
    return Next("WN_EP_DONE")

@step
def STEP_EP_ZP(worker, cycle, env):
    tx,ty,tz = cycle["wn"]["to_cx"], cycle["wn"]["to_cy"], cycle["wn"]["to_cz"]
    case = int(worker.get("chess", {}).get("case_size", 3))
    pz = tz + case
    cmd = ("execute positioned {cx} {cy} {cz} run execute align xz positioned ~0.5 ~ ~0.5 "
           "unless entity @e[tag=chess_piece,distance=..0.49,limit=1] run execute positioned {px} {py} {pz} "
           "run execute align xz positioned ~0.5 ~ ~0.5 if entity @e[tag=chess_piece,tag=b,limit=1,sort=nearest,distance=..0.49] run kill @e[tag=chess_piece,tag=b,limit=1,sort=nearest,distance=..0.49]")
    env.tool("minecraft_control", operation="execute_command", command=cmd.format(cx=tx,cy=ty,cz=tz,px=tx,py=ty,pz=pz))
    return Next("WN_EP_DONE")

@step
def STEP_EP_ZM(worker, cycle, env):
    tx,ty,tz = cycle["wn"]["to_cx"], cycle["wn"]["to_cy"], cycle["wn"]["to_cz"]
    case = int(worker.get("chess", {}).get("case_size", 3))
    pz = tz - case
    cmd = ("execute positioned {cx} {cy} {cz} run execute align xz positioned ~0.5 ~ ~0.5 "
           "unless entity @e[tag=chess_piece,distance=..0.49,limit=1] run execute positioned {px} {py} {pz} "
           "run execute align xz positioned ~0.5 ~ ~0.5 if entity @e[tag=chess_piece,tag=b,limit=1,sort=nearest,distance=..0.49] run kill @e[tag=chess_piece,tag=b,limit=1,sort=nearest,distance=..0.49]")
    env.tool("minecraft_control", operation="execute_command", command=cmd.format(cx=tx,cy=ty,cz=tz,px=tx,py=ty,pz=pz))
    return Next("WN_EP_DONE")

@step
def WN_EP_DONE(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")
