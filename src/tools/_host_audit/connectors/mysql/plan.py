from typing import Dict, Any

def build_plan(profile: str, logs_lines: int) -> Dict[str, Any]:
    cmds = [
        "mysql --version || mariadb --version",
        "mysql -e 'SHOW VARIABLES LIKE \'version\';' || true",
        "mysql -e 'SHOW VARIABLES LIKE \'log_error\';' || true",
        "mysql -e 'SHOW VARIABLES LIKE \'slow_query_log\';' || true",
        "mysql -e 'SHOW VARIABLES LIKE \'slow_query_log_file\';' || true",
        "mysql -e 'SHOW VARIABLES LIKE \'general_log\';' || true",
        "mysql -e 'SHOW VARIABLES LIKE \'general_log_file\';' || true",
        "mysql -e 'SHOW VARIABLES LIKE \'max_connections\';' || true",
        "mysql -e 'SHOW STATUS LIKE \'Threads_connected\';' || true",
        f"LOG_ERR=$(mysql -N -e \"SHOW VARIABLES LIKE 'log_error'\" 2>/dev/null | awk '{{print $2}}') ; if [ -n \"$LOG_ERR\" ] && [ -f \"$LOG_ERR\" ]; then tail -n {max(10, min(logs_lines, 1000))} \"$LOG_ERR\"; fi"
    ]
    return {"ssh_requests": [{"profile": profile, "command": "\n".join(cmds), "desc": "MySQL audit (variables + logs tail limité)"}]}
