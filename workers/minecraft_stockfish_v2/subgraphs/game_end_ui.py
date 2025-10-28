











from py_orch import SubGraph, step, cond, Next, Exit

SUBGRAPH = SubGraph(
    name="GAME_END_UI",
    entry="COND_STATUS",
    exits={"fail": "GEU_LOST", "reinit": "GEU_REINIT"}
)

@cond
def COND_STATUS(worker, cycle, env):
    st = str(cycle.get("endchk", {}).get("status") or "continue").lower()
    if st == "lost":
        return Next("GEU_LOST")
    if st == "win":
        return Next("GEU_WIN")
    return Next("GEU_REINIT")

@step
def GEU_WIN(worker, cycle, env):
    o = worker.get("chess", {}).get("origin_center", {"x":0,"y":64,"z":0})
    x,y,z = int(o.get("x",0)), int(o.get("y",64))+2, int(o.get("z",0))
    cmd = (
        f"summon minecraft:firework_rocket {x} {y} {z} "
        "{LifeTime:40,FireworksItem:{id:\"minecraft:firework_rocket\",Count:1b,tag:{Fireworks:{Flight:2,Explosions:[{Type:0,Colors:[I;16711680],FadeColors:[I;16776960]},{Type:1,Colors:[I;65280],FadeColors:[I;255]}]}}}}"
    )
    env.tool("minecraft_control", operation="batch_commands", delay_ms=0, commands=[
        "title @a[tag=chess_owner] title {\"text\":\"Victoire !\",\"color\":\"gold\"}",
        "title @a[tag=chess_owner] subtitle {\"text\":\"Bien joué\",\"color\":\"green\"}",
        cmd, cmd, cmd
    ])
    return Exit("reinit")

@step
def GEU_LOST(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command",
             command='title @a[tag=chess_owner] title {"text":"Échec et mat","color":"red"}')
    return Exit("fail")

@step
def GEU_REINIT(worker, cycle, env):
    env.transform("set_value", value=True)
    return Exit("reinit")

