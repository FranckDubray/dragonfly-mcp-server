


from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="ENGINE_B_CASTLING",
    entry="COND_CASTLE_DETECT",
    exits={"success": "CA_DONE"}
)

# Detect castling side from best UCI
@cond
def COND_CASTLE_DETECT(worker, cycle, env):
    best = str(cycle.get("eng", {}).get("best_uci") or "")
    if best.startswith("e8g8"):
        return Next("STEP_FIND_H8")
    if best.startswith("e8c8"):
        return Next("STEP_FIND_A8")
    return Exit("success")

# ===== KS path (e8g8): rook h8 -> f8 =====
@step
def STEP_FIND_H8(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"h8"})
    cycle.setdefault("eng", {})["h8_item"] = out.get("items") or []
    return Next("STEP_FIND_F8")

@step
def STEP_FIND_F8(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"f8"})
    cycle.setdefault("eng", {})["f8_item"] = out.get("items") or []
    return Next("KS_GET_F8_CX")

@step
def KS_GET_F8_CX(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("f8_item"), path="0.center.x", default=0)
    cycle.setdefault("eng", {})["f8_cx"] = o.get("result")
    return Next("KS_GET_F8_CY")

@step
def KS_GET_F8_CY(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("f8_item"), path="0.center.y", default=64)
    cycle["eng"]["f8_cy"] = o.get("result")
    return Next("KS_GET_F8_CZ")

@step
def KS_GET_F8_CZ(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("f8_item"), path="0.center.z", default=0)
    cycle["eng"]["f8_cz"] = o.get("result")
    return Next("KS_EXEC_CAPTURE")

@step
def KS_EXEC_CAPTURE(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command",
             command=(
                 f"execute positioned {cycle['eng']['f8_cx']} {cycle['eng']['f8_cy']} {cycle['eng']['f8_cz']} "
                 f"run execute align xz positioned ~0.5 ~ ~0.5 if entity @e[tag=chess_piece,tag=!chess_black_to_move,"
                 f"distance=..{worker['engine']['anim']['target_capture_radius']},limit=1,sort=nearest] "
                 f"run kill @e[tag=chess_piece,tag=!chess_black_to_move,"
                 f"distance=..{worker['engine']['anim']['target_capture_radius']},limit=1,sort=nearest]"
             ))
    return Next("KS_GET_H8_CX")

@step
def KS_GET_H8_CX(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("h8_item"), path="0.center.x", default=0)
    cycle["eng"]["h8_cx"] = o.get("result")
    return Next("KS_GET_H8_CY")

@step
def KS_GET_H8_CY(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("h8_item"), path="0.center.y", default=64)
    cycle["eng"]["h8_cy"] = o.get("result")
    return Next("KS_GET_H8_CZ")

@step
def KS_GET_H8_CZ(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("h8_item"), path="0.center.z", default=0)
    cycle["eng"]["h8_cz"] = o.get("result")
    return Next("KS_TP1")

@step
def KS_TP1(worker, cycle, env):
    env.tool(
        "minecraft_control", operation="execute_command",
        command=(
            f"execute positioned {cycle['eng']['h8_cx']} {cycle['eng']['h8_cy']} {cycle['eng']['h8_cz']} "
            f"run execute align xz positioned ~0.5 ~{worker['engine']['anim']['lift_height']} ~0.5 "
            f"run tp @e[tag=chess_piece,tag=b,limit=1,sort=nearest,distance=..{worker['engine']['anim']['select_from_distance']}] "
            f"{cycle['eng']['f8_cx']} {cycle['eng']['f8_cy']} {cycle['eng']['f8_cz']}"
        )
    )
    return Next("KS_TP2")

@step
def KS_TP2(worker, cycle, env):
    env.tool(
        "minecraft_control", operation="execute_command",
        command=(
            f"execute positioned {cycle['eng']['f8_cx']} {cycle['eng']['f8_cy']} {cycle['eng']['f8_cz']} "
            f"run execute align xz positioned ~0.5 ~ ~0.5 run tp @e[tag=chess_piece,tag=b,limit=1,sort=nearest] ~ ~ ~"
        )
    )
    return Exit("success")

# ===== QS path (e8c8): rook a8 -> d8 =====
@step
def STEP_FIND_A8(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"a8"})
    cycle.setdefault("eng", {})["a8_item"] = out.get("items") or []
    return Next("STEP_FIND_D8")

@step
def STEP_FIND_D8(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"d8"})
    cycle.setdefault("eng", {})["d8_item"] = out.get("items") or []
    return Next("QS_GET_D8_CX")

@step
def QS_GET_D8_CX(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("d8_item"), path="0.center.x", default=0)
    cycle.setdefault("eng", {})["d8_cx"] = o.get("result")
    return Next("QS_GET_D8_CY")

@step
def QS_GET_D8_CY(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("d8_item"), path="0.center.y", default=64)
    cycle["eng"]["d8_cy"] = o.get("result")
    return Next("QS_GET_D8_CZ")

@step
def QS_GET_D8_CZ(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("d8_item"), path="0.center.z", default=0)
    cycle["eng"]["d8_cz"] = o.get("result")
    return Next("QS_EXEC_CAPTURE")

@step
def QS_EXEC_CAPTURE(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command",
             command=(
                 f"execute positioned {cycle['eng']['d8_cx']} {cycle['eng']['d8_cy']} {cycle['eng']['d8_cz']} "
                 f"run execute align xz positioned ~0.5 ~ ~0.5 if entity @e[tag=chess_piece,tag=!chess_black_to_move,"
                 f"distance=..{worker['engine']['anim']['target_capture_radius']},limit=1,sort=nearest] "
                 f"run kill @e[tag=chess_piece,tag=!chess_black_to_move,"
                 f"distance=..{worker['engine']['anim']['target_capture_radius']},limit=1,sort=nearest]"
             ))
    return Next("QS_GET_A8_CX")

@step
def QS_GET_A8_CX(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("a8_item"), path="0.center.x", default=0)
    cycle["eng"]["a8_cx"] = o.get("result")
    return Next("QS_GET_A8_CY")

@step
def QS_GET_A8_CY(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("a8_item"), path="0.center.y", default=64)
    cycle["eng"]["a8_cy"] = o.get("result")
    return Next("QS_GET_A8_CZ")

@step
def QS_GET_A8_CZ(worker, cycle, env):
    o = env.transform("json_ops", op="get", data=cycle.get("eng",{}).get("a8_item"), path="0.center.z", default=0)
    cycle["eng"]["a8_cz"] = o.get("result")
    return Next("QS_TP1")

@step
def QS_TP1(worker, cycle, env):
    env.tool(
        "minecraft_control", operation="execute_command",
        command=(
            f"execute positioned {cycle['eng']['a8_cx']} {cycle['eng']['a8_cy']} {cycle['eng']['a8_cz']} "
            f"run execute align xz positioned ~0.5 ~{worker['engine']['anim']['lift_height']} ~0.5 "
            f"run tp @e[tag=chess_piece,tag=b,limit=1,sort=nearest,distance=..{worker['engine']['anim']['select_from_distance']}] "
            f"{cycle['eng']['d8_cx']} {cycle['eng']['d8_cy']} {cycle['eng']['d8_cz']}"
        )
    )
    return Next("QS_TP2")

@step
def QS_TP2(worker, cycle, env):
    env.tool(
        "minecraft_control", operation="execute_command",
        command=(
            f"execute positioned {cycle['eng']['d8_cx']} {cycle['eng']['d8_cy']} {cycle['eng']['d8_cz']} "
            f"run execute align xz positioned ~0.5 ~ ~0.5 run tp @e[tag=chess_piece,tag=b,limit=1,sort=nearest] ~ ~ ~"
        )
    )
    return Exit("success")

@step
def CA_DONE(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")
