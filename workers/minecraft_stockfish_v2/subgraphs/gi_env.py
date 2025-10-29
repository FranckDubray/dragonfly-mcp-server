



























from py_orch import SubGraph, step, Next, Exit

SUBGRAPH = SubGraph(
    name="GI_ENV",
    entry="STEP_SET_ENV",
    exits={"success": "ENV_DONE"}
)

@step
def STEP_SET_ENV(worker, cycle, env):
    e = worker.get("env", {})
    env.tool("minecraft_control", operation="set_environment",
             weather=e.get("weather"), time=e.get("time"), difficulty=e.get("difficulty"))
    return Next("STEP_MSG_ENV_DONE")

@step
def STEP_MSG_ENV_DONE(worker, cycle, env):
    # Une seule commande sûre (évite try/except et multi-calls): pas d'erreur si aucun joueur tagué
    env.tool("minecraft_control", operation="execute_command", command="say [INIT] Environnement prêt")
    return Exit("success")

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
