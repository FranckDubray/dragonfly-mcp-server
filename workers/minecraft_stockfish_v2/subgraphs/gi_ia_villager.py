












from py_orch import SubGraph, step, Next, Exit

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
    cycle.setdefault("ia", {})["cx"] = out.get("result")
    return Next("STEP_GET_E8_CY")

@step
def STEP_GET_E8_CY(worker, cycle, env):
    e8 = cycle.get("ia", {}).get("e8", [])
    out = env.transform("json_ops", op="get", data=e8, path="0.center.y", default=64)
    cycle.setdefault("ia", {})["cy"] = out.get("result")
    return Next("STEP_GET_E8_CZ")

@step
def STEP_GET_E8_CZ(worker, cycle, env):
    e8 = cycle.get("ia", {}).get("e8", [])
    out = env.transform("json_ops", op="get", data=e8, path="0.center.z", default=0)
    cycle.setdefault("ia", {})["cz"] = out.get("result")
    return Next("STEP_SET_GOLD")

@step
def STEP_SET_GOLD(worker, cycle, env):
    y = int(worker.get("chess", {}).get("y_level", 64))
    cx, cy, cz = cycle.get("ia", {}).get("cx"), cycle.get("ia", {}).get("cy"), cycle.get("ia", {}).get("cz")
    env.tool("minecraft_control", operation="execute_command", command=f"setblock {cx} {y} {cz} minecraft:gold_block")
    return Next("STEP_SUMMON")

@step
def STEP_SUMMON(worker, cycle, env):
    y = int(worker.get("chess", {}).get("y_level", 64))
    cx, cy, cz = cycle.get("ia", {}).get("cx"), cycle.get("ia", {}).get("cy"), cycle.get("ia", {}).get("cz")
    # CustomName JSON direct sans entités HTML
    cmd = (
        "summon minecraft:villager {x} {y} {z} "
        "{{NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,"
        "CustomName:'{{\"text\":\"IA\"}}',CustomNameVisible:1b,Tags:[\"chess_ia\",\"b\"]}}"
    ).format(x=cx, y=y+1.2, z=cz)
    env.tool("minecraft_control", operation="execute_command", command=cmd)
    return Exit("success")

 
 
 
 
 
 
 
 
 
 
 
