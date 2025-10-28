
from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_SPAWN_LOCK_SNAP_B",
    entry="STEP_FILTER_W_BACK_B",
    exits={"success": "SNAP_DONE_B"}
)

@step
def STEP_FILTER_W_BACK_B(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares,
                        predicate={"kind": "in_list", "path": "square", "list": ["a1","b1","c1","d1","e1","f1","g1","h1"]})
    cycle.setdefault("spawn_b", {})["w_back_items"] = out.get("items", [])
    return Next("STEP_TPL_W_BACK_B")

@step
def STEP_TPL_W_BACK_B(worker, cycle, env):
    items = cycle.get("spawn_b", {}).get("w_back_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:0b,'
        'Tags:["chess_piece","w","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, round_coords=True)
    cycle.setdefault("spawn_b", {})["w_back_cmds"] = out.get("commands", [])
    return Next("STEP_FILTER_W_PAWNS_B")

@step
def STEP_FILTER_W_PAWNS_B(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares,
                        predicate={"kind": "in_list", "path": "square", "list": ["a2","b2","c2","d2","e2","f2","g2","h2"]})
    cycle.setdefault("spawn_b", {})["w_pawns_items"] = out.get("items", [])
    return Next("STEP_TPL_W_PAWNS_B")

@step
def STEP_TPL_W_PAWNS_B(worker, cycle, env):
    items = cycle.get("spawn_b", {}).get("w_pawns_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:0b,'
        'Tags:["chess_piece","w","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, round_coords=True)
    cycle.setdefault("spawn_b", {})["w_pawns_cmds"] = out.get("commands", [])
    return Next("STEP_FILTER_B_BACK_B")

@step
def STEP_FILTER_B_BACK_B(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares,
                        predicate={"kind": "in_list", "path": "square", "list": ["a8","b8","c8","d8","e8","f8","g8","h8"]})
    cycle.setdefault("spawn_b", {})["b_back_items"] = out.get("items", [])
    return Next("STEP_TPL_B_BACK_B")

@step
def STEP_TPL_B_BACK_B(worker, cycle, env):
    items = cycle.get("spawn_b", {}).get("b_back_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:15b,'
        'Tags:["chess_piece","b","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, round_coords=True)
    cycle.setdefault("spawn_b", {})["b_back_cmds"] = out.get("commands", [])
    return Next("STEP_FILTER_B_PAWNS_B")

@step
def STEP_FILTER_B_PAWNS_B(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    out = env.transform("array_ops", op="filter", items=squares,
                        predicate={"kind": "in_list", "path": "square", "list": ["a7","b7","c7","d7","e7","f7","g7","h7"]})
    cycle.setdefault("spawn_b", {})["b_pawns_items"] = out.get("items", [])
    return Next("STEP_TPL_B_PAWNS_B")

@step
def STEP_TPL_B_PAWNS_B(worker, cycle, env):
    items = cycle.get("spawn_b", {}).get("b_pawns_items", [])
    tpl = (
        'execute positioned {{center.x}} {{center.y}} {{center.z}} run '
        'summon minecraft:sheep ~ ~1.2 ~ {NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,Color:15b,'
        'Tags:["chess_piece","b","{{square}}"]}'
    )
    out = env.transform("template_map", items=items, template=tpl, round_coords=True)
    cycle.setdefault("spawn_b", {})["b_pawns_cmds"] = out.get("commands", [])
    return Next("STEP_DO_SPAWN_B")

@step
def STEP_DO_SPAWN_B(worker, cycle, env):
    s = cycle.get("spawn_b", {})
    cmds = (s.get("w_back_cmds") or []) + (s.get("w_pawns_cmds") or []) + (s.get("b_back_cmds") or []) + (s.get("b_pawns_cmds") or [])
    env.tool("minecraft_control", operation="batch_commands", delay_ms=2, commands=cmds)
    return Next("STEP_LIST_ENTS_B")

@step
def STEP_LIST_ENTS_B(worker, cycle, env):
    out = env.tool("minecraft_control", operation="list_entities", selector="@e[tag=chess_piece]",
                   fields=["uuid","custom_name","pos","tags"], limit=128)
    cycle.setdefault("mc", {})["raw_b"] = out.get("result") or out.get("items") or []
    return Next("STEP_NORM_B")

@step
def STEP_NORM_B(worker, cycle, env):
    out = env.transform("normalize_entities", items=cycle.get("mc", {}).get("raw_b", []))
    cycle.setdefault("mc", {})["norm_b"] = out.get("items") or []
    return Next("STEP_SORT_B")

@step
def STEP_SORT_B(worker, cycle, env):
    out = env.transform("array_ops", op="sort_by", items=cycle.get("mc", {}).get("norm_b", []), key="pos.y", order="desc")
    cycle["mc"]["sorted_b"] = out.get("items") or []
    return Next("STEP_UNIQ_B")

@step
def STEP_UNIQ_B(worker, cycle, env):
    out = env.transform("array_ops", op="unique_by", items=cycle.get("mc", {}).get("sorted_b", []), key="piece_key")
    cycle["mc"]["dedup_b"] = out.get("items") or []
    return Next("STEP_SNAP_POS_B")

@step
def STEP_SNAP_POS_B(worker, cycle, env):
    out = env.transform("pos_to_square", items=cycle.get("mc", {}).get("dedup_b", []),
                        origin=worker.get("chess", {}).get("origin_center"),
                        axis=worker.get("chess", {}).get("axis"),
                        case_size=worker.get("chess", {}).get("case_size"),
                        epsilon=worker.get("chess", {}).get("epsilon_snap", 0.8))
    cycle.setdefault("prev", {})["positions"] = out.get("map") or {}
    return Next("STEP_MSG_SPAWN_DONE_B")

@step
def STEP_MSG_SPAWN_DONE_B(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command", command="say [INIT] Pieces placed (start position B)")
    return Exit("success")
