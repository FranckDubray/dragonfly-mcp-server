from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_SPAWN_BLACK_PAWNS",
    entry="STEP_FILTER_B_PAWNS",
    exits={"success": "SPAWN_BP_DONE"}
)

@step
def STEP_FILTER_B_PAWNS(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform(
        "array_ops", op="filter", items=squares,
        predicate={"kind": "in_list", "path": "square", "list": ["a7","b7","c7","d7","e7","f7","g7","h7"]}
    )
    cycle.setdefault("spawn", {})["b_pawns_items"] = out.get("items", [])
    return Next("STEP_TPL_B_PAWNS")

@step
def STEP_TPL_B_PAWNS(worker, cycle, env):
    items = cycle.get("spawn", {}).get("b_pawns_items", [])
    pname = (worker.get("pieces", {}) or {}).get("black_pawn", "pion")
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:15b,'
        'CustomName:\'"{{display}}"\',CustomNameVisible:1b,Rotation:[180f,0f],'
        'Tags:["chess_piece","b","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, globals={"display": pname}, round_coords=True)
    cycle.setdefault("spawn", {})["b_pawns_cmds"] = out.get("commands", [])
    return Exit("success")
