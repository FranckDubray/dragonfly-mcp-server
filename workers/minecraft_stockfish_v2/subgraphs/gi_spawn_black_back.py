from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_SPAWN_BLACK_BACK",
    entry="STEP_BB_A8_ITEMS",
    exits={"success": "SPAWN_BB_DONE"}
)

# a8
@step
def STEP_BB_A8_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"a8"})
    cycle.setdefault("spawn", {})["bb_a8_items"] = out.get("items") or []
    return Next("STEP_BB_A8_TPL")

@step
def STEP_BB_A8_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("black_back", {}).get("a8", "tour")
    items = cycle.get("spawn", {}).get("bb_a8_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:15b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[180f,0f],'
        'Tags:["chess_piece","b","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["bb_a8_cmds"] = out.get("commands") or []
    return Next("STEP_BB_B8_ITEMS")

# b8
@step
def STEP_BB_B8_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"b8"})
    cycle.setdefault("spawn", {})["bb_b8_items"] = out.get("items") or []
    return Next("STEP_BB_B8_TPL")

@step
def STEP_BB_B8_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("black_back", {}).get("b8", "cavalier")
    items = cycle.get("spawn", {}).get("bb_b8_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:15b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[180f,0f],'
        'Tags:["chess_piece","b","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["bb_b8_cmds"] = out.get("commands") or []
    return Next("STEP_BB_C8_ITEMS")

# c8
@step
def STEP_BB_C8_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"c8"})
    cycle.setdefault("spawn", {})["bb_c8_items"] = out.get("items") or []
    return Next("STEP_BB_C8_TPL")

@step
def STEP_BB_C8_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("black_back", {}).get("c8", "fou")
    items = cycle.get("spawn", {}).get("bb_c8_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:15b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[180f,0f],'
        'Tags:["chess_piece","b","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["bb_c8_cmds"] = out.get("commands") or []
    return Next("STEP_BB_D8_ITEMS")

# d8
@step
def STEP_BB_D8_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"d8"})
    cycle.setdefault("spawn", {})["bb_d8_items"] = out.get("items") or []
    return Next("STEP_BB_D8_TPL")

@step
def STEP_BB_D8_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("black_back", {}).get("d8", "dame")
    items = cycle.get("spawn", {}).get("bb_d8_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:15b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[180f,0f],'
        'Tags:["chess_piece","b","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["bb_d8_cmds"] = out.get("commands") or []
    return Next("STEP_BB_E8_ITEMS")

# e8
@step
def STEP_BB_E8_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"e8"})
    cycle.setdefault("spawn", {})["bb_e8_items"] = out.get("items") or []
    return Next("STEP_BB_E8_TPL")

@step
def STEP_BB_E8_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("black_back", {}).get("e8", "roi")
    items = cycle.get("spawn", {}).get("bb_e8_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:15b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[180f,0f],'
        'Tags:["chess_piece","b","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["bb_e8_cmds"] = out.get("commands") or []
    return Next("STEP_BB_F8_ITEMS")

# f8
@step
def STEP_BB_F8_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"f8"})
    cycle.setdefault("spawn", {})["bb_f8_items"] = out.get("items") or []
    return Next("STEP_BB_F8_TPL")

@step
def STEP_BB_F8_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("black_back", {}).get("f8", "fou")
    items = cycle.get("spawn", {}).get("bb_f8_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:15b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[180f,0f],'
        'Tags:["chess_piece","b","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["bb_f8_cmds"] = out.get("commands") or []
    return Next("STEP_BB_G8_ITEMS")

# g8
@step
def STEP_BB_G8_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"g8"})
    cycle.setdefault("spawn", {})["bb_g8_items"] = out.get("items") or []
    return Next("STEP_BB_G8_TPL")

@step
def STEP_BB_G8_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("black_back", {}).get("g8", "cavalier")
    items = cycle.get("spawn", {}).get("bb_g8_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:15b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[180f,0f],'
        'Tags:["chess_piece","b","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["bb_g8_cmds"] = out.get("commands") or []
    return Next("STEP_BB_H8_ITEMS")

# h8
@step
def STEP_BB_H8_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"h8"})
    cycle.setdefault("spawn", {})["bb_h8_items"] = out.get("items") or []
    return Next("STEP_BB_H8_TPL")

@step
def STEP_BB_H8_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("black_back", {}).get("h8", "tour")
    items = cycle.get("spawn", {}).get("bb_h8_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:15b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[180f,0f],'
        'Tags:["chess_piece","b","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["bb_h8_cmds"] = out.get("commands") or []
    return Next("STEP_BB_CONCAT")

# concat black back commands
@step
def STEP_BB_CONCAT(worker, cycle, env):
    lists = [
        cycle.get("spawn", {}).get("bb_a8_cmds") or [],
        cycle.get("spawn", {}).get("bb_b8_cmds") or [],
        cycle.get("spawn", {}).get("bb_c8_cmds") or [],
        cycle.get("spawn", {}).get("bb_d8_cmds") or [],
        cycle.get("spawn", {}).get("bb_e8_cmds") or [],
        cycle.get("spawn", {}).get("bb_f8_cmds") or [],
        cycle.get("spawn", {}).get("bb_g8_cmds") or [],
        cycle.get("spawn", {}).get("bb_h8_cmds") or [],
    ]
    out = env.transform("array_concat", lists=lists)
    cycle.setdefault("spawn", {})["b_back_cmds"] = out.get("items") or []
    return Exit("success")
