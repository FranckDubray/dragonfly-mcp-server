from typing import Dict, Any

def build_plan(profile: str, logs_lines: int) -> Dict[str, Any]:
    cmds = [
        "apache2ctl -v 2>/dev/null || httpd -v 2>/dev/null || apachectl -v 2>/dev/null || true",
        # conf dump limité
        "apache2ctl -S 2>/dev/null | head -n 300 || httpd -S 2>/dev/null | head -n 300 || apachectl -S 2>/dev/null | head -n 300 || true",
        # chemins de conf connus
        "for f in /etc/apache2/apache2.conf /etc/httpd/conf/httpd.conf; do test -f $f && head -n 200 $f; done || true",
        # logs
        f"for f in /var/log/apache2/error.log /var/log/httpd/error_log; do test -f $f && tail -n {max(50, min(logs_lines, 2000))} $f; done || true",
    ]
    return {"ssh_requests": [{"profile": profile, "command": "\n".join(cmds), "desc": "Apache audit (version, vhosts, conf head, logs tail)"}]}
