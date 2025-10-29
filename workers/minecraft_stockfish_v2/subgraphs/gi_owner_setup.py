from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_OWNER_SETUP",
    entry="STEP_CLEAR_OWNERS",
    exits={"success": "OWN_DONE"}
)

@step
def STEP_CLEAR_OWNERS(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command", command="tag @a[tag=chess_owner] remove chess_owner")
    return Next("STEP_TAG_OWNER")

@step
def STEP_TAG_OWNER(worker, cycle, env):
    # Tag the nearest player within 100 blocks anywhere (safer for init)
    env.tool("minecraft_control", operation="execute_command", command="tag @p[distance=..100] add chess_owner")
    return Next("STEP_SCOREBOARD_INIT")

@step
def STEP_SCOREBOARD_INIT(worker, cycle, env):
    w = worker.get("wand", {})
    env.tool("minecraft_control", operation="batch_commands", delay_ms=10, commands=[
        f"scoreboard objectives add {w.get('uses_objective','wand_uses')} dummy",
        f"scoreboard objectives add {w.get('state_objective','wand_state')} dummy",
        f"scoreboard players set @a[tag=chess_owner] {w.get('uses_objective','wand_uses')} 0",
        f"scoreboard players set @a[tag=chess_owner] {w.get('state_objective','wand_state')} 0",
    ])
    return Next("STEP_GIVE_WAND")

@step
def STEP_GIVE_WAND(worker, cycle, env):
    env.tool("minecraft_control", operation="batch_commands", delay_ms=5, commands=[
        "item replace entity @a[tag=chess_owner] weapon.mainhand with minecraft:stick 1",
        "replaceitem entity @a[tag=chess_owner] weapon.mainhand minecraft:stick 1",
        "give @a[tag=chess_owner] minecraft:stick 1"
    ])
    return Next("STEP_ADVENTURE")

@step
def STEP_ADVENTURE(worker, cycle, env):
    env.tool(
        "minecraft_control",
        operation="execute_command",
        command="execute as @a[tag=chess_owner] run gamemode adventure @s"
    )
    return Exit("success")
