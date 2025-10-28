
from datetime import datetime, timezone

def utcnow_str() -> str:
    # Close to previous format used in orchestrator DB
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
