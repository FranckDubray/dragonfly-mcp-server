

from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_PLATFORM_BOARD",
    entry="STEP_COMPUTE_BOUNDS",
    exits={"success": "BOARD_DONE"}
)

@step
def STEP_COMPUTE_BOUNDS(worker, cycle, env):
    o = worker.get("chess", {}).get("origin_center", {"x":0,"z":0,"y":64})
    x1 = int(o.get("x",0) - 1)
    z1 = int(o.get("z",0) - 1)
    x2 = x1 + 23
    z2 = z1 + 23
    out = env.transform("set_value", value={"x1":x1,"z1":z1,"x2":x2,"z2":z2})
    cycle.setdefault("plat", {}).update(out.get("result") or {})
    return Next("STEP_BOARD_COORDS")

@step
def STEP_BOARD_COORDS(worker, cycle, env):
    out = env.transform("board_coords",
                        origin=worker.get("chess", {}).get("origin_center"),
                        axis=worker.get("chess", {}).get("axis"),
                        case_size=worker.get("chess", {}).get("case_size"),
                        y_level=worker.get("chess", {}).get("y_level"),
                        white_near_origin=worker.get("chess", {}).get("white_near_origin"))
    cycle.setdefault("mc", {}).setdefault("board", {})["squares"] = out.get("squares") or []
    return Next("STEP_TPL_PAINT")

@step
def STEP_TPL_PAINT(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("template_map", items=squares,
                        template="execute positioned {{center.x}} {{center.y}} {{center.z}} run fill ~-1 ~ ~-1 ~1 ~ ~1 {{block}}",
                        color_map={"light": "white_concrete", "dark": "black_concrete"},
                        round_coords=True)
    cycle.setdefault("mc", {})["paint_cmds"] = out.get("commands") or []
    return Next("STEP_DO_PAINT")

@step
def STEP_DO_PAINT(worker, cycle, env):
    cmds = cycle.get("mc", {}).get("paint_cmds", [])
    env.tool("minecraft_control", operation="batch_commands", delay_ms=2, commands=cmds)
    return Next("STEP_MSG_BOARD_DONE")

@step
def STEP_MSG_BOARD_DONE(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command", command="say [INIT] Board painted")
    return Exit("success")
