from typing import Dict, Any, List

def build_plan(profile: str, logs_lines: int, paths_hint: List[str]) -> Dict[str, Any]:
    cmds = [
        "lsb_release -a || cat /etc/os-release",
        "uname -a",
        "uptime",
        "df -h | head -n 50",
        "free -m || vmstat -s",
        "top -b -n 1 | head -n 30",
        "ps -eo pid,ppid,cmd:100 --sort=-%mem | head -n 30",
        # Réseau/ports
        "ss -lnt | head -n 50 || netstat -lnt | head -n 50",
        # Pare-feu
        "ufw status verbose || true",
        "(command -v nft >/dev/null && nft list ruleset | head -n 200) || (iptables -L -n | head -n 200) || true",
        # SSH service
        "systemctl is-enabled ssh || systemctl is-enabled sshd || true",
        "systemctl status ssh --no-pager | head -n 60 || systemctl status sshd --no-pager | head -n 60 || true",
        # Logs critiques
        f"journalctl -p 3 -xn | tail -n {max(10, min(logs_lines, 500))}",
        # Packages (échantillon)
        "if command -v dpkg >/dev/null; then dpkg -l | head -n 200; elif command -v rpm >/dev/null; then rpm -qa | head -n 200; fi",
    ]
    for p in paths_hint[:5]:
        cmds.append(f"ls -la {p} | head -n 100")
    return {"ssh_requests": [{"profile": profile, "command": "\n".join(cmds), "desc": "Ubuntu audit compact"}]}
