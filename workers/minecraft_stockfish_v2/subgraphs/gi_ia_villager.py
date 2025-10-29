from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_IA_VILLAGER",
    entry="STEP_FIND_E8",
    exits={"success": "IA_DONE"}
)

@step
def STEP_FIND_E8(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    e8 = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"e8"}).get("items", [])
    cycle.setdefault("ia", {})["e8"] = e8
    return Next("STEP_GET_E8_CX")

@step
def STEP_GET_E8_CX(worker, cycle, env):
    e8 = cycle.get("ia", {}).get("e8", [])
    out = env.transform("json_ops", op="get", data=e8, path="0.center.x", default=0)
    cycle.setdefault("ia", {})["cx"] = int(out.get("result") or 0)
    return Next("STEP_GET_E8_CY")

@step
def STEP_GET_E8_CY(worker, cycle, env):
    e8 = cycle.get("ia", {}).get("e8", [])
    out = env.transform("json_ops", op="get", data=e8, path="0.center.y", default=64)
    cycle.setdefault("ia", {})["cy"] = int(out.get("result") or 64)
    return Next("STEP_GET_E8_CZ")

@step
def STEP_GET_E8_CZ(worker, cycle, env):
    e8 = cycle.get("ia", {}).get("e8", [])
    out = env.transform("json_ops", op="get", data=e8, path="0.center.z", default=0)
    cycle.setdefault("ia", {})["cz"] = int(out.get("result") or 0)
    return Next("STEP_PREP_BOUNDS")

@step
def STEP_PREP_BOUNDS(worker, cycle, env):
    p = cycle.get("plat", {})
    data = {
        "x1": int(p.get("x1", 0)),
        "x2": int(p.get("x2", 0)),
        "z1": int(p.get("z1", 0)),
        "z2": int(p.get("z2", 0)),
        "case": int(worker.get("chess", {}).get("case_size", 3)),
        "y": int(worker.get("chess", {}).get("y_level", 64)),
        "axis": str(worker.get("chess", {}).get("axis", "+x")),
    }
    out = env.transform("set_value", value=data)
    cycle.setdefault("ia", {}).update(out.get("result") or {})
    return Next("COND_AXIS")

@cond
def COND_AXIS(worker, cycle, env):
    axis = str(cycle.get("ia", {}).get("axis") or "+x")
    if axis in ["+x", "-x"]:
        return Next("COND_Z_DIR")
    return Next("COND_X_DIR")

@cond
def COND_Z_DIR(worker, cycle, env):
    cz = int(cycle.get("ia", {}).get("cz", 0))
    z1 = int(cycle.get("ia", {}).get("z1", 0))
    z2 = int(cycle.get("ia", {}).get("z2", 0))
    # If nearer to z1 -> go further toward z1 (decrease z). If nearer to z2 (black side), go +z.
    if abs(cz - z1) <= abs(cz - z2):
        return Next("STEP_SET_SPOT_ZM")
    return Next("STEP_SET_SPOT_ZP")

@cond
def COND_X_DIR(worker, cycle, env):
    cx = int(cycle.get("ia", {}).get("cx", 0))
    x1 = int(cycle.get("ia", {}).get("x1", 0))
    x2 = int(cycle.get("ia", {}).get("x2", 0))
    if abs(cx - x1) <= abs(cx - x2):
        return Next("STEP_SET_SPOT_XM")
    return Next("STEP_SET_SPOT_XP")

@step
def STEP_SET_SPOT_ZM(worker, cycle, env):
    cx = int(cycle["ia"]["cx"]); y = int(cycle["ia"]["y"]); cz = int(cycle["ia"]["cz"]); sz = int(cycle["ia"]["case"])
    gx, gz = cx, cz - sz
    env.tool("minecraft_control", operation="execute_command", command=f"setblock {gx} {y} {gz} minecraft:gold_block")
    cycle.setdefault("ia", {})["spot"] = {"x": gx, "y": y, "z": gz}
    return Next("STEP_SUMMON")

@step
def STEP_SET_SPOT_ZP(worker, cycle, env):
    cx = int(cycle["ia"]["cx"]); y = int(cycle["ia"]["y"]); cz = int(cycle["ia"]["cz"]); sz = int(cycle["ia"]["case"])
    gx, gz = cx, cz + sz
    env.tool("minecraft_control", operation="execute_command", command=f"setblock {gx} {y} {gz} minecraft:gold_block")
    cycle.setdefault("ia", {})["spot"] = {"x": gx, "y": y, "z": gz}
    return Next("STEP_SUMMON")

@step
def STEP_SET_SPOT_XM(worker, cycle, env):
    cx = int(cycle["ia"]["cx"]); y = int(cycle["ia"]["y"]); cz = int(cycle["ia"]["cz"]); sx = int(cycle["ia"]["case"])
    gx, gz = cx - sx, cz
    env.tool("minecraft_control", operation="execute_command", command=f"setblock {gx} {y} {gz} minecraft:gold_block")
    cycle.setdefault("ia", {})["spot"] = {"x": gx, "y": y, "z": gz}
    return Next("STEP_SUMMON")

@step
def STEP_SET_SPOT_XP(worker, cycle, env):
    cx = int(cycle["ia"]["cx"]); y = int(cycle["ia"]["y"]); cz = int(cycle["ia"]["cz"]); sx = int(cycle["ia"]["case"])
    gx, gz = cx + sx, cz
    env.tool("minecraft_control", operation="execute_command", command=f"setblock {gx} {y} {gz} minecraft:gold_block")
    cycle.setdefault("ia", {})["spot"] = {"x": gx, "y": y, "z": gz}
    return Next("STEP_SUMMON")

@step
def STEP_SUMMON(worker, cycle, env):
    s = cycle.get("ia", {}).get("spot", {})
    x = int(s.get("x", 0)); y = int(s.get("y", 64)); z = int(s.get("z", 0))
    cmd = f"""summon minecraft:villager {x} {y+1} {z} {{NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,CustomName:'"IA"',CustomNameVisible:1b,Tags:[\"chess_ia\",\"b\"]}}"""
    env.tool("minecraft_control", operation="execute_command", command=cmd)
    return Exit("success")
