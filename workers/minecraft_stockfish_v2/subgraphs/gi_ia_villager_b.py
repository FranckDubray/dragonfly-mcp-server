
from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_IA_VILLAGER_B",
    entry="STEP_FIND_E8_B",
    exits={"success": "IA_DONE_B"}
)

@step
def STEP_FIND_E8_B(worker, cycle, env):
    squares = cycle.get("mc", {}).get("board", {}).get("squares", [])
    e8 = env.transform("array_ops", op="filter", items=squares, predicate={"kind":"eq","path":"square","value":"e8"}).get("items", [])
    cycle.setdefault("ia_b", {})["e8"] = e8
    return Next("STEP_GET_E8_CX_B")

@step
def STEP_GET_E8_CX_B(worker, cycle, env):
    e8 = cycle.get("ia_b", {}).get("e8", [])
    out = env.transform("json_ops", op="get", data=e8, path="0.center.x", default=0)
    cycle.setdefault("ia_b", {})["cx"] = out.get("result")
    return Next("STEP_GET_E8_CY_B")

@step
def STEP_GET_E8_CY_B(worker, cycle, env):
    e8 = cycle.get("ia_b", {}).get("e8", [])
    out = env.transform("json_ops", op="get", data=e8, path="0.center.y", default=64)
    cycle.setdefault("ia_b", {})["cy"] = out.get("result")
    return Next("STEP_GET_E8_CZ_B")

@step
def STEP_GET_E8_CZ_B(worker, cycle, env):
    e8 = cycle.get("ia_b", {}).get("e8", [])
    out = env.transform("json_ops", op="get", data=e8, path="0.center.z", default=0)
    cycle.setdefault("ia_b", {})["cz"] = out.get("result")
    return Next("STEP_SET_GOLD_B")

@step
def STEP_SET_GOLD_B(worker, cycle, env):
    y = int(worker.get("chess", {}).get("y_level", 64))
    cx, cy, cz = cycle.get("ia_b", {}).get("cx"), cycle.get("ia_b", {}).get("cy"), cycle.get("ia_b", {}).get("cz")
    env.tool("minecraft_control", operation="execute_command", command=f"setblock {cx} {y} {cz} minecraft:gold_block")
    return Next("STEP_SUMMON_B")

@step
def STEP_SUMMON_B(worker, cycle, env):
    y = int(worker.get("chess", {}).get("y_level", 64))
    cx, cy, cz = cycle.get("ia_b", {}).get("cx"), cycle.get("ia_b", {}).get("cy"), cycle.get("ia_b", {}).get("cz")
    nbt = '{NoAI:1b,NoGravity:1b,Invulnerable:1b,PersistenceRequired:1b,CustomName:\'{"text":"IA"}\',CustomNameVisible:1b,Tags:["chess_ia","b"]}'
    cmd = "summon minecraft:villager {x} {y} {z} {nbt}".format(x=cx, y=y+1.2, z=cz, nbt=nbt)
    env.tool("minecraft_control", operation="execute_command", command=cmd)
    return Exit("success")
