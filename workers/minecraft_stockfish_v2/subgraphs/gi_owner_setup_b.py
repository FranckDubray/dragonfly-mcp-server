
from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_OWNER_SETUP_B",
    entry="STEP_CLEAR_OWNERS_B",
    exits={"success": "OWN_DONE_B"}
)

@step
def STEP_CLEAR_OWNERS_B(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command", command="tag @a[tag=chess_owner] remove chess_owner")
    return Next("STEP_TAG_OWNER_B")

@step
def STEP_TAG_OWNER_B(worker, cycle, env):
    o = worker.get("chess", {}).get("origin_center", {"x":0,"z":0}); y = int(worker.get("chess", {}).get("y_level", 64))
    env.tool("minecraft_control", operation="execute_command", command=f"tag @p[x={o['x']},y={y},z={o['z']},distance=..20] add chess_owner")
    return Next("STEP_SCOREBOARD_INIT_B")

@step
def STEP_SCOREBOARD_INIT_B(worker, cycle, env):
    w = worker.get("wand", {})
    env.tool("minecraft_control", operation="batch_commands", delay_ms=10, commands=[
        f"scoreboard objectives add {w.get('uses_objective','wand_uses')} dummy",
        f"scoreboard objectives add {w.get('state_objective','wand_state')} dummy",
        f"scoreboard players set @a[tag=chess_owner] {w.get('uses_objective','wand_uses')} 0",
        f"scoreboard players set @a[tag=chess_owner] {w.get('state_objective','wand_state')} 0",
    ])
    return Next("STEP_GIVE_WAND_B")

@step
def STEP_GIVE_WAND_B(worker, cycle, env):
    env.tool("minecraft_control", operation="batch_commands", delay_ms=5, commands=[
        "item replace entity @a[tag=chess_owner] weapon.mainhand with minecraft:stick 1",
        "replaceitem entity @a[tag=chess_owner] weapon.mainhand minecraft:stick 1",
        "give @a[tag=chess_owner] minecraft:stick 1"
    ])
    return Next("STEP_ADVENTURE_B")

@step
def STEP_ADVENTURE_B(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command", command=f"gamemode adventure @a[tag=chess_owner]")
    return Exit("success")
