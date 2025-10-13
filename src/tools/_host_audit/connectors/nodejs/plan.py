from typing import Dict, Any

def build_plan(profile: str) -> Dict[str, Any]:
    cmds = [
        "node -v || true",
        "npm -v || true",
        "which pm2 >/dev/null 2>&1 && pm2 ls || true",
    ]
    return {"ssh_requests": [{"profile": profile, "command": "\n".join(cmds), "desc": "Node.js audit (versions, pm2 process list)"}]}
