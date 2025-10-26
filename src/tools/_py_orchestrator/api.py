
from typing import Dict, Any
from .api_router import route as _route

# Backward-compatible export

def start_or_control(params: dict) -> Dict[str, Any]:
    return _route(params)
