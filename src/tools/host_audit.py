import json, os
from typing import Any, Dict

from ._host_audit.connectors.ubuntu.plan import build_plan as build_plan_ubuntu
from ._host_audit.connectors.mysql.plan import build_plan as build_plan_mysql
from ._host_audit.connectors.symfony.plan import build_plan as build_plan_symfony
from ._host_audit.connectors.nginx.plan import build_plan as build_plan_nginx
from ._host_audit.connectors.apache.plan import build_plan as build_plan_apache
from ._host_audit.connectors.nodejs.plan import build_plan as build_plan_nodejs
from ._host_audit.connectors.phpfpm.plan import build_plan as build_plan_phpfpm

def spec():
    here = os.path.dirname(__file__)
    spec_path = os.path.abspath(os.path.join(here, '..', 'tool_specs', 'host_audit.json'))
    with open(spec_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Ce tool NE lance pas de commandes: il génère des plans compacts pour ssh_admin/macos local.

def run(operation: str, limit: int = 50, logs_lines: int = 200, profile: str | None = None, paths_hint: list[str] | None = None, **kwargs) -> Dict[str, Any]:
    paths_hint = paths_hint or []
    if operation == 'macos_local':
        cmds = [
            {"cmd": "sw_vers", "desc": "Version macOS"},
            {"cmd": "sysctl -n machdep.cpu.brand_string", "desc": "CPU"},
            {"cmd": "system_profiler SPHardwareDataType -detailLevel mini", "desc": "Résumé hardware"},
            {"cmd": "system_profiler SPApplicationsDataType -detailLevel mini | head -n 200", "desc": "Applications (échantillon)"},
            {"cmd": "brew --version || true", "desc": "Homebrew version"},
            {"cmd": "brew list --versions | head -n 200 || true", "desc": "Packages Homebrew (échantillon)"},
            {"cmd": "mdfind 'kMDItemFSName == \"Microsoft Word.app\"' -onlyin /Applications || true", "desc": "Word installé ?"}
        ]
        return {"operation": operation, "plan": {"local_commands": cmds}, "returned_count": len(cmds), "total_count": len(cmds), "truncated": False}

    if operation == 'ubuntu_ssh_plan':
        if not profile:
            return {"operation": operation, "errors": [{"code": "invalid_parameters", "message": "profile requis", "scope": "tool", "recoverable": True}], "returned_count": 0, "total_count": 0, "truncated": False}
        plan = build_plan_ubuntu(profile, logs_lines, paths_hint)
        return {"operation": operation, "plan": plan, "returned_count": 1, "total_count": 1, "truncated": False}

    if operation == 'mysql_ssh_plan':
        if not profile:
            return {"operation": operation, "errors": [{"code": "invalid_parameters", "message": "profile requis", "scope": "tool", "recoverable": True}], "returned_count": 0, "total_count": 0, "truncated": False}
        plan = build_plan_mysql(profile, logs_lines)
        return {"operation": operation, "plan": plan, "returned_count": 1, "total_count": 1, "truncated": False}

    if operation == 'symfony_ssh_plan':
        if not profile:
            return {"operation": operation, "errors": [{"code": "invalid_parameters", "message": "profile requis", "scope": "tool", "recoverable": True}], "returned_count": 0, "total_count": 0, "truncated": False}
        plan = build_plan_symfony(profile)
        return {"operation": operation, "plan": plan, "returned_count": 1, "total_count": 1, "truncated": False}

    if operation == 'nginx_ssh_plan':
        if not profile:
            return {"operation": operation, "errors": [{"code": "invalid_parameters", "message": "profile requis", "scope": "tool", "recoverable": True}], "returned_count": 0, "total_count": 0, "truncated": False}
        plan = build_plan_nginx(profile, logs_lines)
        return {"operation": operation, "plan": plan, "returned_count": 1, "total_count": 1, "truncated": False}

    if operation == 'apache_ssh_plan':
        if not profile:
            return {"operation": operation, "errors": [{"code": "invalid_parameters", "message": "profile requis", "scope": "tool", "recoverable": True}], "returned_count": 0, "total_count": 0, "truncated": False}
        plan = build_plan_apache(profile, logs_lines)
        return {"operation": operation, "plan": plan, "returned_count": 1, "total_count": 1, "truncated": False}

    if operation == 'nodejs_ssh_plan':
        if not profile:
            return {"operation": operation, "errors": [{"code": "invalid_parameters", "message": "profile requis", "scope": "tool", "recoverable": True}], "returned_count": 0, "total_count": 0, "truncated": False}
        plan = build_plan_nodejs(profile)
        return {"operation": operation, "plan": plan, "returned_count": 1, "total_count": 1, "truncated": False}

    if operation == 'phpfpm_ssh_plan':
        if not profile:
            return {"operation": operation, "errors": [{"code": "invalid_parameters", "message": "profile requis", "scope": "tool", "recoverable": True}], "returned_count": 0, "total_count": 0, "truncated": False}
        plan = build_plan_phpfpm(profile, logs_lines)
        return {"operation": operation, "plan": plan, "returned_count": 1, "total_count": 1, "truncated": False}

    return {"operation": operation, "errors": [{"code": "invalid_parameters", "message": "operation inconnue", "scope": "tool", "recoverable": False}], "returned_count": 0, "total_count": 0, "truncated": False}
