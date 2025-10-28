
from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_LEVER_FW_B",
    entry="STEP_COMPUTE_POS_B",
    exits={"success": "LEVER_DONE_B"}
)

@step
def STEP_COMPUTE_POS_B(worker, cycle, env):
    p = cycle.get("plat", {})
    y = int(worker.get("chess", {}).get("y_level", 64))
    lx = int(p.get("x2", 0)) + 2
    lz = int(p.get("z1", 0)) + 12
    out = env.transform("set_value", value={"x": lx, "z": lz, "y1": y})
    cycle.setdefault("lever", {}).update(out.get("result") or {})
    return Next("STEP_SET_GOLD_B")

@step
def STEP_SET_GOLD_B(worker, cycle, env):
    lv = cycle.get("lever", {})
    env.tool("minecraft_control", operation="execute_command",
             command=f"setblock {lv['x']} {lv['y1']} {lv['z']} minecraft:gold_block")
    return Next("STEP_SET_LEVER_B")

@step
def STEP_SET_LEVER_B(worker, cycle, env):
    lv = cycle.get("lever", {})
    env.tool("minecraft_control", operation="execute_command",
             command=f"setblock {lv['x']} {lv['y1']+1} {lv['z']} minecraft:lever[face=floor,facing=west,powered=false]")
    return Next("STEP_MSG_B")

@step
def STEP_MSG_B(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command", command="say [INIT] Lever placed (B)")
    return Exit("success")
