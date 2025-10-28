

from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_LEVER_FW",
    entry="STEP_COMPUTE_POS",
    exits={"success": "LEVER_DONE"}
)

@step
def STEP_COMPUTE_POS(worker, cycle, env):
    p = cycle.get("plat", {})
    y = int(worker.get("chess", {}).get("y_level", 64))
    lx = int(p.get("x2", 0)) + 2
    lz = int(p.get("z1", 0)) + 12
    out = env.transform("set_value", value={"x": lx, "z": lz, "y1": y})
    cycle.setdefault("lever", {}).update(out.get("result") or {})
    return Next("STEP_SET_GOLD")

@step
def STEP_SET_GOLD(worker, cycle, env):
    lv = cycle.get("lever", {})
    env.tool("minecraft_control", operation="execute_command",
             command=f"setblock {lv['x']} {lv['y1']} {lv['z']} minecraft:gold_block")
    return Next("STEP_SET_LEVER")

@step
def STEP_SET_LEVER(worker, cycle, env):
    lv = cycle.get("lever", {})
    env.tool("minecraft_control", operation="execute_command",
             command=f"setblock {lv['x']} {lv['y1']+1} {lv['z']} minecraft:lever[face=floor,facing=west,powered=false]")
    return Next("STEP_MSG")

@step
def STEP_MSG(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command", command="say [INIT] Lever placed")
    return Exit("success")
