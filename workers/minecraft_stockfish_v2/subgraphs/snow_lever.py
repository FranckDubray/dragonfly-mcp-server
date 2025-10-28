















from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="SNOW_LEVER",
    entry="STEP_PLACE_AND_CHECK",
    exits={"success": "SL_DONE"}
)

@step
def STEP_PLACE_AND_CHECK(worker, cycle, env):
    # place a dedicated lever near main lever (z+2)
    lv = cycle.get("lever", {})
    y = int(worker.get("chess", {}).get("y_level", 64))
    x, z = int(lv.get("x")), int(lv.get("z"))+2
    cycle.setdefault("clean_lever", {})["x"], cycle["clean_lever"]["z"] = x, z
    env.tool("minecraft_control", operation="execute_command", command=f"setblock {x} {y} {z} minecraft:gold_block")
    return Next("STEP_SET_CLEAN_LEVER")

@step
def STEP_SET_CLEAN_LEVER(worker, cycle, env):
    y = int(worker.get("chess", {}).get("y_level", 64))
    cl = cycle.get("clean_lever", {})
    env.tool("minecraft_control", operation="execute_command", command=f"setblock {cl.get('x')} {y+1} {cl.get('z')} minecraft:lever[face=floor,facing=west]")
    return Next("STEP_CHECK_POWERED")

@step
def STEP_CHECK_POWERED(worker, cycle, env):
    y = int(worker.get("chess", {}).get("y_level", 64))
    cl = cycle.get("clean_lever", {})
    out = env.tool("minecraft_control", operation="execute_command",
                   command=f"execute if block {cl.get('x')} {y+1} {cl.get('z')} minecraft:lever[powered=true] run say SNOW_ON")
    cycle.setdefault("snowlever", {})["check"] = out.get("result") or out.get("content") or ""
    return Next("COND_POWERED")

@cond
def COND_POWERED(worker, cycle, env):
    if "SNOW_ON" in str(cycle.get("snowlever", {}).get("check") or ""):
        return Next("STEP_CLEAR_SNOW")
    return Next("SL_DONE")

@step
def STEP_CLEAR_SNOW(worker, cycle, env):
    p = cycle.get("plat", {})
    y = int(worker.get("chess", {}).get("y_level", 64))
    env.tool("minecraft_control", operation="execute_command",
             command=f"fill {p['x1']} {y+1} {p['z1']} {p['x2']} {y+2} {p['z2']} minecraft:air replace minecraft:snow")
    return Next("STEP_RESET_CLEAN_LEVER")

@step
def STEP_RESET_CLEAN_LEVER(worker, cycle, env):
    y = int(worker.get("chess", {}).get("y_level", 64))
    cl = cycle.get("clean_lever", {})
    env.tool("minecraft_control", operation="execute_command",
             command=f"setblock {cl.get('x')} {y+1} {cl.get('z')} minecraft:lever[face=floor,facing=west]")
    return Next("SL_DONE")

@step
def SL_DONE(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")
