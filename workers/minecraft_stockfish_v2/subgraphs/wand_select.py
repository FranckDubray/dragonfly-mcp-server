
























from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="WAND_SELECT",
    entry="STEP_CLEAR_PREV",
    exits={"success": "STEP_MSG_SELECTED"}
)

@step
def STEP_CLEAR_PREV(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command", command="tag @e[tag=chess_selected] remove chess_selected")
    return Next("STEP_GET_D")

@step
def STEP_GET_D(worker, cycle, env):
    d = float(worker.get("wand", {}).get("select_distance_threshold", 1.4))
    out = env.transform("set_value", value=d)
    cycle.setdefault("wand", {})["sel_d"] = out.get("result")
    return Next("STEP_RAY_1")

@step
def STEP_RAY_1(worker, cycle, env):
    d = cycle.get("wand", {}).get("sel_d")
    tpl = ("execute as @a[tag=chess_owner] at @s rotated as @s positioned ^ ^ ^{i}  "
           "if entity @e[tag=chess_piece,tag=w,distance=..{d}] run tag @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{d}] add chess_selected")
    out = env.transform("format_template", template=tpl, context={"i": 1, "d": d})
    cycle.setdefault("wand", {})["cmd1"] = out.get("result")
    return Next("STEP_RAY_2")

@step
def STEP_RAY_2(worker, cycle, env):
    d = cycle.get("wand", {}).get("sel_d")
    tpl = ("execute as @a[tag=chess_owner] at @s rotated as @s positioned ^ ^ ^{i}  "
           "if entity @e[tag=chess_piece,tag=w,distance=..{d}] run tag @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{d}] add chess_selected")
    out = env.transform("format_template", template=tpl, context={"i": 2, "d": d})
    cycle.setdefault("wand", {})["cmd2"] = out.get("result")
    return Next("STEP_RAY_3")

@step
def STEP_RAY_3(worker, cycle, env):
    d = cycle.get("wand", {}).get("sel_d")
    tpl = ("execute as @a[tag=chess_owner] at @s rotated as @s positioned ^ ^ ^{i}  "
           "if entity @e[tag=chess_piece,tag=w,distance=..{d}] run tag @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{d}] add chess_selected")
    out = env.transform("format_template", template=tpl, context={"i": 3, "d": d})
    cycle.setdefault("wand", {})["cmd3"] = out.get("result")
    return Next("STEP_RAY_4")

@step
def STEP_RAY_4(worker, cycle, env):
    d = cycle.get("wand", {}).get("sel_d")
    tpl = ("execute as @a[tag=chess_owner] at @s rotated as @s positioned ^ ^ ^{i}  "
           "if entity @e[tag=chess_piece,tag=w,distance=..{d}] run tag @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{d}] add chess_selected")
    out = env.transform("format_template", template=tpl, context={"i": 4, "d": d})
    cycle.setdefault("wand", {})["cmd4"] = out.get("result")
    return Next("STEP_RAY_5")

@step
def STEP_RAY_5(worker, cycle, env):
    d = cycle.get("wand", {}).get("sel_d")
    tpl = ("execute as @a[tag=chess_owner] at @s rotated as @s positioned ^ ^ ^{i}  "
           "if entity @e[tag=chess_piece,tag=w,distance=..{d}] run tag @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{d}] add chess_selected")
    out = env.transform("format_template", template=tpl, context={"i": 5, "d": d})
    cycle.setdefault("wand", {})["cmd5"] = out.get("result")
    return Next("STEP_RAY_MAX_BUILD")

@step
def STEP_RAY_MAX_BUILD(worker, cycle, env):
    maxb = int(worker.get("wand", {}).get("select_max_blocks", 6))
    out = env.transform("set_value", value=maxb)
    cycle.setdefault("wand", {})["sel_max"] = out.get("result")
    return Next("STEP_RAY_MAX")

@step
def STEP_RAY_MAX(worker, cycle, env):
    d = cycle.get("wand", {}).get("sel_d")
    i = cycle.get("wand", {}).get("sel_max")
    tpl = ("execute as @a[tag=chess_owner] at @s rotated as @s positioned ^ ^ ^{i}  "
           "if entity @e[tag=chess_piece,tag=w,distance=..{d}] run tag @e[tag=chess_piece,tag=w,limit=1,sort=nearest,distance=..{d}] add chess_selected")
    out = env.transform("format_template", template=tpl, context={"i": i, "d": d})
    cycle.setdefault("wand", {})["cmdm"] = out.get("result")
    return Next("STEP_BUILD_CMDS")

@step
def STEP_BUILD_CMDS(worker, cycle, env):
    cmds = [
        cycle.get("wand", {}).get("cmd1"),
        cycle.get("wand", {}).get("cmd2"),
        cycle.get("wand", {}).get("cmd3"),
        cycle.get("wand", {}).get("cmd4"),
        cycle.get("wand", {}).get("cmd5"),
        cycle.get("wand", {}).get("cmdm"),
    ]
    out = env.transform("set_value", value=cmds)
    cycle.setdefault("wand", {})["ray_cmds"] = out.get("result")
    return Next("STEP_DO_RAYCAST")

@step
def STEP_DO_RAYCAST(worker, cycle, env):
    cmds = cycle.get("wand", {}).get("ray_cmds") or []
    env.tool("minecraft_control", operation="batch_commands", delay_ms=0, commands=cmds)
    return Next("STEP_LIST_SELECTED")

@step
def STEP_LIST_SELECTED(worker, cycle, env):
    out = env.tool("minecraft_control", operation="list_entities", selector="@e[tag=chess_selected]",
                   fields=["uuid","pos","tags"], limit=1)
    cycle.setdefault("wand", {})["sel"] = out.get("result") or out.get("items") or []
    return Next("COND_HAS_SELECTION")

@cond
def COND_HAS_SELECTION(worker, cycle, env):
    if cycle.get("wand", {}).get("sel"):
        return Next("STEP_MSG_SELECTED")
    return Next("STEP_WAIT")

@step
def STEP_WAIT(worker, cycle, env):
    # Pause de polling en fin de boucle (5s par défaut). Utilise select_poll_ms si fourni, sinon move_poll_ms.
    turns = worker.get("turns", {})
    ms = int(turns.get("select_poll_ms", turns.get("move_poll_ms", 5000)))
    env.transform("sleep", ms=ms)
    return Next("STEP_CLEAR_PREV")

@step
def STEP_MSG_SELECTED(worker, cycle, env):
    # Utiliser une commande sûre (say) pour éviter les erreurs de title
    env.tool(
        "minecraft_control",
        operation="execute_command",
        command='say [WAND] Piece sélectionnée'
    )
    return Exit("success")
