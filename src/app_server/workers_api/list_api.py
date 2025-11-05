




















from __future__ import annotations
from typing import Dict, Any, Optional

# Couche d'appel au tool py_orchestrator via ses modules Python (pas d'HTTP intermédiaire)
# Tente 2 chemins d'import (avec et sans préfixe src.) pour s'adapter à l'environnement.

async def get_list(leader: Optional[str] = None) -> Dict[str, Any]:
    try:
        try:
            from src.tools._py_orchestrator.api_router import route as py_route
        except Exception:
            from tools._py_orchestrator.api_router import route as py_route
        res = py_route({"operation": "list"})
        if not isinstance(res, dict):
            return {"accepted": False, "status": "error", "message": "list: invalid response type"}
        res.setdefault("workers", [])
        return res
    except Exception as e:
        return {"accepted": False, "status": "error", "message": f"list failed: {str(e)[:200]}"}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
