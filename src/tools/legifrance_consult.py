"""Bootstrap for legifrance_consult."""
from typing import Dict, Any
from ._legifrance_consult.api import route_request
from ._legifrance_consult import spec as _spec

def run(**params) -> Dict[str, Any]:
    op = params.get("operation")
    if not op:
        return {"error": "Operation required"}
    
    clean_params = {k: v for k, v in params.items() if k != "operation"}
    
    # Map 'article_ids' (list) to 'ids' (expected by utils/cli)
    if "article_ids" in clean_params:
        clean_params["ids"] = clean_params.pop("article_ids")
        
    return route_request(op, **clean_params)

def spec() -> Dict[str, Any]:
    return _spec()
