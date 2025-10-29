from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_SPAWN_WHITE_PAWNS",
    entry="STEP_FILTER_W_PAWNS",
    exits={"success": "SPAWN_WP_DONE"}
)

@step
def STEP_FILTER_W_PAWNS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform(
        "array_ops", op="filter", items=squares,
        predicate={"kind": "in_list", "path": "square", "list": ["a2","b2","c2","d2","e2","f2","g2","h2"]}
    )
    cycle.setdefault("spawn", {})["w_pawns_items"] = out.get("items", [])
    return Next("STEP_TPL_W_PAWNS")

@step
def STEP_TPL_W_PAWNS(worker, cycle, env):
    items = cycle.get("spawn", {}).get("w_pawns_items", [])
    pname = (worker.get("pieces", {}) or {}).get("white_pawn", "pion")
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:0b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[0f,0f],'
        'Tags:["chess_piece","w","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": pname}, round_coords=True)
    cycle.setdefault("spawn", {})["w_pawns_cmds"] = out.get("commands", [])
    return Exit("success")
