from typing import Dict, Any

def build_plan(profile: str) -> Dict[str, Any]:
    cmds = [
        "php -v || true",
        "php -m | head -n 100 || true",
        "composer --version || true",
        "if [ -f bin/console ]; then php bin/console about || true; php bin/console debug:router --format=json | head -n 500 || true; fi",
        "grep -R --line-number -E '^\\s*(path:|methods:|prefix:)' -n config/routes | head -n 200 || true"
    ]
    return {"ssh_requests": [{"profile": profile, "command": "\n".join(cmds), "desc": "Symfony audit (console + YAML routes)"}]}
