


from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="ENGINE_SNAPSHOT_TURN",
    entry="STEP_LIST",
    exits={"success": "ES_EXIT"}
)

@step
def STEP_LIST(worker, cycle, env):
    out = env.tool("minecraft_control", operation="list_entities", selector="@e[tag=chess_piece]",
                   fields=["uuid","custom_name","pos","tags"], limit=64)
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
    return Next("STEP_SNAP")

@step
def STEP_SNAP(worker, cycle, env):
    out = env.transform("pos_to_square", items=cycle.get("mc", {}).get("dedup", []),
                        origin=worker.get("chess", {}).get("origin_center"),
                        axis=worker.get("chess", {}).get("axis"),
                        case_size=worker.get("chess", {}).get("case_size"),
                        epsilon=worker.get("chess", {}).get("epsilon_snap", 0.8))
    cycle.setdefault("prev", {})["positions"] = out.get("map") or {}
    return Next("STEP_GET_NOW")

@step
def STEP_GET_NOW(worker, cycle, env):
    out = env.tool("date", operation="now", format="iso", timezone="UTC")
    cycle.setdefault("game", {})["last_turn_ts"] = out.get("result")
    return Next("STEP_CLEAR_BTAG")

@step
def STEP_CLEAR_BTAG(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command", command="tag @e[tag=chess_black_to_move] remove chess_black_to_move")
    return Next("ES_EXIT")

@step
def ES_EXIT(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")
