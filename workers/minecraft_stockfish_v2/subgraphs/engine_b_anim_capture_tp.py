



from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="ENGINE_B_ANIM_CAPTURE_TP",
    entry="STEP_SELECT_BLACK",
    exits={"success": "AC_DONE"}
)

@step
def STEP_SELECT_BLACK(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command",
             command=f"execute positioned {cycle['eng']['from_cx']} {cycle['eng']['from_cy']} {cycle['eng']['from_cz']} run tag @e[tag=chess_piece,tag=b,limit=1,sort=nearest,distance=..{worker['engine']['anim']['select_from_distance']}] add chess_black_to_move")
    return Next("STEP_CAPTURE_WHITE")

@step
def STEP_CAPTURE_WHITE(worker, cycle, env):
    r = worker.get("engine", {}).get("anim", {}).get("target_capture_radius", 0.49)
    tx,ty,tz = cycle["eng"]["to_cx"], cycle["eng"]["to_cy"], cycle["eng"]["to_cz"]
    env.tool("minecraft_control", operation="execute_command",
             command=f"execute positioned {tx} {ty} {tz} run execute align xz positioned ~0.5 ~ ~0.5 if block ~ ~-1 ~ minecraft:white_concrete if entity @e[tag=chess_piece,tag=!chess_black_to_move,distance=..{r},limit=1,sort=nearest] run kill @e[tag=chess_piece,tag=!chess_black_to_move,distance=..{r},limit=1,sort=nearest]")
    return Next("STEP_CAPTURE_BLACK")

@step
def STEP_CAPTURE_BLACK(worker, cycle, env):
    r = worker.get("engine", {}).get("anim", {}).get("target_capture_radius", 0.49)
    tx,ty,tz = cycle["eng"]["to_cx"], cycle["eng"]["to_cy"], cycle["eng"]["to_cz"]
    env.tool("minecraft_control", operation="execute_command",
             command=f"execute positioned {tx} {ty} {tz} run execute align xz positioned ~0.5 ~ ~0.5 if block ~ ~-1 ~ minecraft:black_concrete if entity @e[tag=chess_piece,tag=!chess_black_to_move,distance=..{r},limit=1,sort=nearest] run kill @e[tag=chess_piece,tag=!chess_black_to_move,distance=..{r},limit=1,sort=nearest]")
    return Next("STEP_TP_LIFT")

@step
def STEP_TP_LIFT(worker, cycle, env):
    h = worker.get("engine", {}).get("anim", {}).get("lift_height", 1.2)
    tx,ty,tz = cycle["eng"]["to_cx"], cycle["eng"]["to_cy"], cycle["eng"]["to_cz"]
    env.tool("minecraft_control", operation="execute_command",
             command=f"execute positioned {tx} {ty} {tz} run execute align xz positioned ~0.5 ~{h} ~0.5 run tp @e[tag=chess_black_to_move,limit=1,sort=nearest] ~ ~ ~")
    return Next("STEP_TP_SNAP")

@step
def STEP_TP_SNAP(worker, cycle, env):
    tx,ty,tz = cycle["eng"]["to_cx"], cycle["eng"]["to_cy"], cycle["eng"]["to_cz"]
    env.tool("minecraft_control", operation="execute_command",
             command=f"execute positioned {tx} {ty} {tz} run execute align xz positioned ~0.5 ~ ~0.5 run tp @e[tag=chess_black_to_move,limit=1,sort=nearest] ~ ~ ~")
    return Next("AC_DONE")

@step
def AC_DONE(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")

 
 
 
