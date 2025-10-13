Objectif: détecter anti-patterns de performance probables dans ce tool MCP.
Rends JSON: {findings:[{id,rule,severity,path,range,explain,fix,anchors}]}
Règles: heavy_loop, regex_compile_in_loop, sync_io_in_async, concat_str_in_loop, unbounded_glob.
Max 10 findings. Explications <= 120 caractères. Anchors-only.
