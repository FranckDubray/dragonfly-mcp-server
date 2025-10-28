






































































































from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="BOARD_PROTECT",
    entry="STEP_TPL_PAINT",
    exits={"success": "BP_DONE"}
)

@step
def STEP_TPL_PAINT(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("template_map", items=squares,
                        template="execute positioned {{center.x}} {{center.y}} {{center.z}} run fill ~-1 ~ ~-1 ~1 ~ ~1 {{block}}",
                        color_map={"light": "white_concrete", "dark": "black_concrete"},
                        round_coords=True)
    cycle.setdefault("bp", {})["paint_cmds"] = out.get("commands") or []
    return Next("STEP_DO_PAINT")

@step
def STEP_DO_PAINT(worker, cycle, env):
    cmds = cycle.get("bp", {}).get("paint_cmds") or []
    env.tool("minecraft_control", operation="batch_commands", delay_ms=2, commands=cmds)
    return Next("STEP_RESET_LEVER")

@step
def STEP_RESET_LEVER(worker, cycle, env):
    lv = cycle.get("lever", {})
    y = int(worker.get("chess", {}).get("y_level", 64)) + 1
    env.tool("minecraft_control", operation="execute_command",
             command=f"setblock {lv.get('x')} {y} {lv.get('z')} minecraft:lever[face=floor,facing=west]")
    return Exit("success")

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
