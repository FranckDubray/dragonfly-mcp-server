from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_SPAWN_WHITE_BACK",
    entry="STEP_WB_A1_ITEMS",
    exits={"success": "SPAWN_WB_DONE"}
)

# a1
@step
def STEP_WB_A1_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"a1"})
    cycle.setdefault("spawn", {})["wb_a1_items"] = out.get("items") or []
    return Next("STEP_WB_A1_TPL")

@step
def STEP_WB_A1_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("white_back", {}).get("a1", "tour")
    items = cycle.get("spawn", {}).get("wb_a1_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:0b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[0f,0f],'
        'Tags:["chess_piece","w","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["wb_a1_cmds"] = out.get("commands") or []
    return Next("STEP_WB_B1_ITEMS")

# b1
@step
def STEP_WB_B1_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"b1"})
    cycle.setdefault("spawn", {})["wb_b1_items"] = out.get("items") or []
    return Next("STEP_WB_B1_TPL")

@step
def STEP_WB_B1_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("white_back", {}).get("b1", "cavalier")
    items = cycle.get("spawn", {}).get("wb_b1_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:0b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[0f,0f],'
        'Tags:["chess_piece","w","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["wb_b1_cmds"] = out.get("commands") or []
    return Next("STEP_WB_C1_ITEMS")

# c1
@step
def STEP_WB_C1_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"c1"})
    cycle.setdefault("spawn", {})["wb_c1_items"] = out.get("items") or []
    return Next("STEP_WB_C1_TPL")

@step
def STEP_WB_C1_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("white_back", {}).get("c1", "fou")
    items = cycle.get("spawn", {}).get("wb_c1_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:0b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[0f,0f],'
        'Tags:["chess_piece","w","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["wb_c1_cmds"] = out.get("commands") or []
    return Next("STEP_WB_D1_ITEMS")

# d1
@step
def STEP_WB_D1_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"d1"})
    cycle.setdefault("spawn", {})["wb_d1_items"] = out.get("items") or []
    return Next("STEP_WB_D1_TPL")

@step
def STEP_WB_D1_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("white_back", {}).get("d1", "dame")
    items = cycle.get("spawn", {}).get("wb_d1_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:0b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[0f,0f],'
        'Tags:["chess_piece","w","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["wb_d1_cmds"] = out.get("commands") or []
    return Next("STEP_WB_E1_ITEMS")

# e1
@step
def STEP_WB_E1_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"e1"})
    cycle.setdefault("spawn", {})["wb_e1_items"] = out.get("items") or []
    return Next("STEP_WB_E1_TPL")

@step
def STEP_WB_E1_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("white_back", {}).get("e1", "roi")
    items = cycle.get("spawn", {}).get("wb_e1_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:0b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[0f,0f],'
        'Tags:["chess_piece","w","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["wb_e1_cmds"] = out.get("commands") or []
    return Next("STEP_WB_F1_ITEMS")

# f1
@step
def STEP_WB_F1_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"f1"})
    cycle.setdefault("spawn", {})["wb_f1_items"] = out.get("items") or []
    return Next("STEP_WB_F1_TPL")

@step
def STEP_WB_F1_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("white_back", {}).get("f1", "fou")
    items = cycle.get("spawn", {}).get("wb_f1_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:0b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[0f,0f],'
        'Tags:["chess_piece","w","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["wb_f1_cmds"] = out.get("commands") or []
    return Next("STEP_WB_G1_ITEMS")

# g1
@step
def STEP_WB_G1_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"g1"})
    cycle.setdefault("spawn", {})["wb_g1_items"] = out.get("items") or []
    return Next("STEP_WB_G1_TPL")

@step
def STEP_WB_G1_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("white_back", {}).get("g1", "cavalier")
    items = cycle.get("spawn", {}).get("wb_g1_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:0b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[0f,0f],'
        'Tags:["chess_piece","w","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["wb_g1_cmds"] = out.get("commands") or []
    return Next("STEP_WB_H1_ITEMS")

# h1
@step
def STEP_WB_H1_ITEMS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"h1"})
    cycle.setdefault("spawn", {})["wb_h1_items"] = out.get("items") or []
    return Next("STEP_WB_H1_TPL")

@step
def STEP_WB_H1_TPL(worker, cycle, env):
    disp = (worker.get("pieces", {}) or {}).get("white_back", {}).get("h1", "tour")
    items = cycle.get("spawn", {}).get("wb_h1_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:0b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[0f,0f],'
        'Tags:["chess_piece","w","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": disp}, round_coords=True)
    cycle.setdefault("spawn", {})["wb_h1_cmds"] = out.get("commands") or []
    return Next("STEP_WB_CONCAT")

@step
def STEP_WB_CONCAT(worker, cycle, env):
    lists = [
        cycle.get("spawn", {}).get("wb_a1_cmds") or [],
        cycle.get("spawn", {}).get("wb_b1_cmds") or [],
        cycle.get("spawn", {}).get("wb_c1_cmds") or [],
        cycle.get("spawn", {}).get("wb_d1_cmds") or [],
        cycle.get("spawn", {}).get("wb_e1_cmds") or [],
        cycle.get("spawn", {}).get("wb_f1_cmds") or [],
        cycle.get("spawn", {}).get("wb_g1_cmds") or [],
        cycle.get("spawn", {}).get("wb_h1_cmds") or [],
    ]
    out = env.transform("array_concat", lists=lists)
    cycle.setdefault("spawn", {})["w_back_cmds"] = out.get("items") or []
    return Exit("success")
