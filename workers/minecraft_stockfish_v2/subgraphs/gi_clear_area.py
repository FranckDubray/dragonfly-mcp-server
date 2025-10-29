from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_CLEAR_AREA",
    entry="STEP_COMPUTE_AABB",
    exits={"success": "CLR_DONE"}
)

@step
def STEP_COMPUTE_AABB(worker, cycle, env):
    chess = worker.get("chess", {})
    o = chess.get("origin_center", {"x": 0, "z": 0})
    y = int(chess.get("y_level", 64))
    case = int(chess.get("case_size", 3))
    width = int(8 * case)
    x1 = int(o.get("x", 0) - 1)
    z1 = int(o.get("z", 0) - 1)
    x2 = x1 + width - 1
    z2 = z1 + width - 1
    cymin = y + int(chess.get("clear_y_min_offset", -5))
    cymax = y + int(chess.get("clear_y_max_offset", 5))
    out = env.transform("set_value", value={"x1": x1, "z1": z1, "x2": x2, "z2": z2, "y_min": cymin, "y_max": cymax, "width": width})
    cycle.setdefault("plat", {}).update(out.get("result") or {})
    return Next("STEP_TP_OWNER_SAFE")

@step
def STEP_TP_OWNER_SAFE(worker, cycle, env):
    # Pas de TP joueur à l'init (laisse le joueur où il est)
    env.transform("set_value", value=True)
    return Next("STEP_FILL_AIR")

@step
def STEP_FILL_AIR(worker, cycle, env):
    p = cycle.get("plat", {})
    env.tool("minecraft_control", operation="execute_command",
             command=f"fill {p['x1']} {p['y_min']} {p['z1']} {p['x2']} {p['y_max']} {p['z2']} minecraft:air")
    return Next("STEP_KILL_AABB")

@step
def STEP_KILL_AABB(worker, cycle, env):
    p = cycle.get("plat", {})
    dx = p['x2'] - p['x1']
    dy = p['y_max'] - p['y_min']
    dz = p['z2'] - p['z1']
    # Exclure nos entités de jeu (pièces et IA)
    cmd = "kill @e[type=!player,tag=!chess_piece,tag=!chess_ia,x={x1},y={y1},z={z1},dx={dx},dy={dy},dz={dz}]".format(
        x1=p['x1'], y1=p['y_min'], z1=p['z1'], dx=dx, dy=dy, dz=dz
    )
    env.tool("minecraft_control", operation="execute_command", command=cmd)
    return Next("STEP_MSG_CLEAR_DONE")

@step
def STEP_MSG_CLEAR_DONE(worker, cycle, env):
    env.tool("minecraft_control", operation="execute_command",
             command="say [INIT] Clear done (AABB safe)")
    return Exit("success")
