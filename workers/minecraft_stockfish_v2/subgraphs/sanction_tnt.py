from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="SANCTION_TNT",
    entry="STEP_MSG",
    exits={"success": "ST_EXIT"}
)

@step
def STEP_MSG(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command",
             command="title @a[tag=chess_owner] actionbar {\"text\":\"Sanction\",\"color\":\"red\"}")
    return Next("COND_WARN")

@cond
def COND_WARN(worker, cycle, env):
    mode = str(worker.get("sanction", {}).get("mode") or "tnt").lower()
    if mode == "warn":
        return Next("STEP_WARN_SFX")
    return Next("STEP_SURV")

@step
def STEP_WARN_SFX(worker, cycle, env):
    env.tool("minecraft_control", operation="batch_commands", delay_ms=0, commands=[
        "playsound minecraft:block.note_block.bass master @a[tag=chess_owner] ~ ~ ~ 1 0.5",
        "title @a[tag=chess_owner] title {\\\"text\\\":\\\"Coup interdit\\\" ,\\\"color\\\":\\\"red\\\"}",
        "title @a[tag=chess_owner] subtitle {\\\"text\\\":\\\"(avertissement)\\\" ,\\\"color\\\":\\\"yellow\\\"}",
    ])
    return Exit("success")

@step
def STEP_SURV(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command",
             command="gamemode survival @a[tag=chess_owner]")
    return Next("STEP_FIRE")

@step
def STEP_FIRE(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command",
             command="execute as @a[tag=chess_owner] run data merge entity @s {Fire:200}")
    return Next("STEP_FORCELOAD_ADD")

@step
def STEP_FORCELOAD_ADD(worker, cycle, env):
    chunk = worker.get("sanction", {}).get("tnt_chunk", {})
    env.tool("minecraft_control", operation="execute_command",
             command=f"forceload add {chunk.get('cx')} {chunk.get('cz')}")
    return Next("STEP_CLEAR_AREA")

@step
def STEP_CLEAR_AREA(worker, cycle, env):
    area = worker.get("sanction", {}).get("area", {})
    mn, mx = area.get("min", {}), area.get("max", {})
    env.tool("minecraft_control", operation="execute_command",
             command=f"fill {mn.get('x')} {mn.get('y')} {mn.get('z')} {mx.get('x')} {mx.get('y')} {mx.get('z')} minecraft:air")
    return Next("STEP_PREP_TNT_CMDS")

@step
def STEP_PREP_TNT_CMDS(worker, cycle, env):
    # Build list via a transform (1 call/step)
    tnts = worker.get("sanction", {}).get("tnt", []) or []
    fuse = int(worker.get("sanction", {}).get("tnt_fuse_ticks", 80))
    # Use template_map-like transform: if unavailable, fall back to set_value on prebuilt list
    cmds = [f"summon minecraft:tnt {t.get('x')} {t.get('y')} {t.get('z')} {{Fuse:{fuse}b}}" for t in tnts if t]
    out = env.transform("set_value", value=cmds)
    cycle.setdefault("tnt", {})["cmds"] = out.get("result") or cmds
    return Next("STEP_IGNITE_TNT")

@step
def STEP_IGNITE_TNT(worker, cycle, env):
    cmds = cycle.get("tnt", {}).get("cmds") or []
    env.tool("minecraft_control", operation="batch_commands", delay_ms=0, commands=cmds)
    return Next("COND_TP_NEEDED")

@cond
def COND_TP_NEEDED(worker, cycle, env):
    tnts = worker.get("sanction", {}).get("tnt", [])
    if (tnts or []):
        return Next("STEP_TP_OWNER")
    return Next("STEP_FORCELOAD_REMOVE")

@step
def STEP_TP_OWNER(worker, cycle, env):
    tnts = worker.get("sanction", {}).get("tnt", [])
    t0 = (tnts or [{}])[0]
    env.tool("minecraft_control", operation="execute_command",
             command=f"tp @a[tag=chess_owner] {t0.get('x')} {t0.get('y')} {t0.get('z')}")
    return Next("STEP_FORCELOAD_REMOVE")

@step
def STEP_FORCELOAD_REMOVE(worker, cycle, env):
    chunk = worker.get("sanction", {}).get("tnt_chunk", {})
    env.tool("minecraft_control", operation="execute_command",
             command=f"forceload remove {chunk.get('cx')} {chunk.get('cz')}")
    return Next("ST_EXIT")

@step
def ST_EXIT(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("success")
