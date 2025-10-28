
from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_CLEAR_AREA",
    entry="STEP_COMPUTE_AABB",
    exits={"success": "CLR_DONE"}
)

@step
def STEP_COMPUTE_AABB(worker, cycle, env):
    # Compute and store AABB using a single transform
    o = worker.get("chess", {}).get("origin_center", {"x":0,"z":0})
    y = int(worker.get("chess", {}).get("y_level", 64))
    x1 = int(o.get("x",0) - 1)
    z1 = int(o.get("z",0) - 1)
    x2 = x1 + 23
    z2 = z1 + 23
    cymin = y + int(worker.get("chess", {}).get("clear_y_min_offset", -5))
    cymax = y + int(worker.get("chess", {}).get("clear_y_max_offset", 5))
    out = env.transform("set_value", value={"x1":x1,"z1":z1,"x2":x2,"z2":z2,"y_min":cymin,"y_max":cymax})
    cycle.setdefault("plat", {}).update(out.get("result") or {})
    return Next("STEP_CLEAR_AIR")

@step
def STEP_CLEAR_AIR(worker, cycle, env):
    p = cycle.get("plat", {})
    env.tool("minecraft_control", operation="execute_command",
             command=f"fill {p['x1']} {p['y_min']} {p['z1']} {p['x2']} {p['y_max']} {p['z2']} minecraft:air")
    return Next("STEP_KILL_AABB")

@step
def STEP_KILL_AABB(worker, cycle, env):
    p = cycle.get("plat", {})
    dx = p['x2'] - p['x1']
    dy = p['y_max'] - p['y_min']
    dz = p['z2'] - p['z1']
    cmd = "kill @e[type=!player,x={x1},y={y1},z={z1},dx={dx},dy={dy},dz={dz}]".format(
        x1=p['x1'], y1=p['y_min'], z1=p['z1'], dx=dx, dy=dy, dz=dz
    )
    env.tool("minecraft_control", operation="execute_command", command=cmd)
    return Next("STEP_MSG_CLEAR_DONE")

@step
def STEP_MSG_CLEAR_DONE(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command",
             command="say [INIT] Clear done (10 layers, AABB kill non-players)")
    return Exit("success")
