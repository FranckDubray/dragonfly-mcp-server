
# List workers (reuse JSON orchestrator implementation)
from .._orchestrator.api_list import list_workers as list_workers_json

def list_workers():
    return list_workers_json()
