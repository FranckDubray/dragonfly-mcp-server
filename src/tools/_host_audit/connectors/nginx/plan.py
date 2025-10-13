from typing import Dict, Any

def build_plan(profile: str, logs_lines: int) -> Dict[str, Any]:
    cmds = [
        "nginx -v 2>&1 || true",
        "nginx -T | head -n 400 || (test -f /etc/nginx/nginx.conf && head -n 400 /etc/nginx/nginx.conf) || true",
        f"test -f /var/log/nginx/error.log && tail -n {max(50, min(logs_lines, 2000))} /var/log/nginx/error.log || true",
        f"test -f /var/log/nginx/access.log && tail -n {max(50, min(logs_lines, 2000))} /var/log/nginx/access.log || true",
    ]
    return {"ssh_requests": [{"profile": profile, "command": "\n".join(cmds), "desc": "Nginx audit (version, conf head, logs tail)"}]}
