





from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="TURN_LEVER_RESET",
    entry="COND_HAS_LEVER",
    exits={"success": "TLR_DONE"}
)

@cond
def COND_HAS_LEVER(worker, cycle, env):
    if cycle.get("lever", {}):
        return Next("STEP_RESET_ON_START")
    return Exit("success")

@step
def STEP_RESET_ON_START(worker, cycle, env):
    # Reset lever to powered=false right after a turn starts (upon TURN_TIMER success)
    lv = cycle.get("lever", {})
    y = int(worker.get("chess", {}).get("y_level", 64)) + 1
    env.tool(
        "minecraft_control",
        operation="execute_command",
        command=f"setblock {lv.get('x')} {y} {lv.get('z')} minecraft:lever[face=floor,facing=west,powered=false]"
    )
    return Exit("success")

 
 
 
