from typing import Dict, Any

def build_plan(profile: str, logs_lines: int) -> Dict[str, Any]:
    cmds = [
        "php-fpm -v 2>/dev/null || php-fpm8.2 -v 2>/dev/null || php-fpm7.4 -v 2>/dev/null || true",
        # Test conf
        "php-fpm -tt 2>/dev/null | head -n 200 || php-fpm8.2 -tt 2>/dev/null | head -n 200 || php-fpm7.4 -tt 2>/dev/null | head -n 200 || true",
        # Pools connus
        "for d in /etc/php/*/fpm/pool.d /etc/php-fpm.d; do test -d $d && for f in $d/*.conf; do head -n 120 \"$f\"; done; done || true",
        # Logs
        f"for f in /var/log/php*-fpm.log /var/log/php7*-fpm.log /var/log/php8*-fpm.log; do test -f $f && tail -n {max(50, min(logs_lines, 2000))} $f; done || true",
    ]
    return {"ssh_requests": [{"profile": profile, "command": "\n".join(cmds), "desc": "PHP-FPM audit (version, pools, conf test, logs tail)"}]}
