from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_SPAWN_COMBINE_AND_SNAP",
    entry="STEP_DO_SPAWN",
    exits={"success": "SNAP_DONE"}
)

@step
def STEP_DO_SPAWN(worker, cycle, env):
    s = cycle.get("spawn", {})
    cmds = (s.get("w_back_cmds") or []) + (s.get("w_pawns_cmds") or []) + (s.get("b_back_cmds") or []) + (s.get("b_pawns_cmds") or [])
    env.tool("minecraft_control", operation="batch_commands", delay_ms=2, commands=cmds)
    return Next("STEP_LIST_ENTS")

@step
def STEP_LIST_ENTS(worker, cycle, env):
    out = env.tool(
        "minecraft_control", operation="list_entities", selector="@e[tag=chess_piece]",
        fields=["uuid", "custom_name", "pos", "tags"], limit=128
    )
    cycle.setdefault("mc", {})["raw"] = out.get("result") or out.get("items") or []
    return Next("STEP_NORM")

@step
def STEP_NORM(worker, cycle, env):
    out = env.transform("normalize_entities", items=cycle.get("mc", {}).get("raw", []))
    cycle.setdefault("mc", {})["norm"] = out.get("items") or []
    return Next("STEP_SORT")

@step
def STEP_SORT(worker, cycle, env):
    out = env.transform("array_ops", op="sort_by", items=cycle.get("mc", {}).get("norm", []), key="pos.y", order="desc")
    cycle["mc"]["sorted"] = out.get("items") or []
    return Next("STEP_UNIQ")

@step
def STEP_UNIQ(worker, cycle, env):
    out = env.transform("array_ops", op="unique_by", items=cycle.get("mc", {}).get("sorted", []), key="piece_key")
    cycle["mc"]["dedup"] = out.get("items") or []
    return Next("STEP_SNAP_POS")

@step
def STEP_SNAP_POS(worker, cycle, env):
    out = env.transform(
        "pos_to_square", items=cycle.get("mc", {}).get("dedup", []),
        origin=worker.get("chess", {}).get("origin_center"),
        axis=worker.get("chess", {}).get("axis"),
        case_size=worker.get("chess", {}).get("case_size"),
        epsilon=worker.get("chess", {}).get("epsilon_snap", 0.8)
    )
    cycle.setdefault("prev", {})["positions"] = out.get("map") or {}
    return Exit("success")
