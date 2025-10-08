from __future__ import annotations
import sys
import json
import importlib
import pkgutil
import time
from hashlib import sha1
from typing import Dict, Any, List, Set
from pathlib import Path
import logging

from fastapi import Request, Response

from .safe_json import sanitize_for_json

LOG = logging.getLogger(__name__)

registry: Dict[str, Dict[str, Any]] = {}
_tool_id_counter = 10000
_last_scan_time = 0.0
_tools_dir_mtime = 0.0
_tools_file_set: Set[str] = set()


def get_registry() -> Dict[str, Dict[str, Any]]:
    return registry


def get_tools_directory_info() -> Dict[str, Any]:
    try:
        import tools as tools_package
        tools_path = Path(tools_package.__path__[0])
        if not tools_path.exists():
            return {"mtime": 0, "file_set": set(), "file_count": 0}
        tool_files = set()
        max_mtime = tools_path.stat().st_mtime
        for item in tools_path.iterdir():
            if item.name.startswith('_'):
                continue
            if item.is_file() and item.suffix == '.py':
                tool_files.add(item.name)
                max_mtime = max(max_mtime, item.stat().st_mtime)
            elif item.is_dir():
                tool_files.add(f"{item.name}/")
                max_mtime = max(max_mtime, item.stat().st_mtime)
                for subfile in item.rglob('*.py'):
                    max_mtime = max(max_mtime, subfile.stat().st_mtime)
        return {"mtime": max_mtime, "file_set": tool_files, "file_count": len(tool_files), "directory_exists": True}
    except Exception as e:
        LOG.warning(f"Could not get tools directory info: {e}")
        return {"mtime": 0, "file_set": set(), "file_count": 0, "directory_exists": False}


def discover_tools():
    global registry, _last_scan_time, _tools_dir_mtime, _tool_id_counter, _tools_file_set
    _last_scan_time = time.time()
    tools_info = get_tools_directory_info()
    _tools_dir_mtime = tools_info["mtime"]
    current_file_set = tools_info["file_set"]
    added_files = current_file_set - _tools_file_set
    removed_files = _tools_file_set - current_file_set
    _tools_file_set = current_file_set
    if added_files:
        LOG.info(f"🆕 New tool files detected: {added_files}")
    if removed_files:
        LOG.info(f"🗑️ Removed tool files detected: {removed_files}")
    old_count = len(registry)
    registry.clear()
    _tool_id_counter = 10000
    try:
        import tools as tools_package
        tools_path = tools_package.__path__
        modules = []
        for finder, name, ispkg in pkgutil.iter_modules(tools_path):
            if name.startswith('_') or name == '__init__':
                continue
            try:
                module_name = f'tools.{name}'
                LOG.info(f"🔍 Discovering {'package' if ispkg else 'module'}: {name}")
                if module_name in sys.modules:
                    LOG.info(f"♻️ Reloading existing {'package' if ispkg else 'module'}: {name}")
                    importlib.reload(sys.modules[module_name])
                    module = sys.modules[module_name]
                else:
                    LOG.info(f"📥 Importing new {'package' if ispkg else 'module'}: {name}")
                    module = importlib.import_module(module_name)
                modules.append((name, module, ispkg))
            except Exception as e:
                LOG.error(f"❌ Failed to import {'package' if ispkg else 'module'} {name}: {e}")
        LOG.info(f"🔍 Found {len(modules)} potential tool modules/packages")
        for module_name, module, ispkg in modules:
            if hasattr(module, 'run') and hasattr(module, 'spec'):
                try:
                    spec = module.spec()
                    tool_name = spec['function']['name']
                    display_name = spec['function'].get('displayName', tool_name)
                    tool_id = _tool_id_counter; _tool_id_counter += 1
                    registry[tool_name] = {
                        "id": tool_id,
                        "name": tool_name,
                        "regName": tool_name,
                        "displayName": display_name,
                        "description": spec['function']['description'],
                        "json": json.dumps(spec, separators=(",", ":"), ensure_ascii=False),
                        "func": module.run
                    }
                    pkg_info = " (package)" if ispkg else ""
                    LOG.info(f"✅ Registered tool: {tool_name} (ID: {tool_id}) (from {module_name}{pkg_info}) as '{display_name}'")
                except Exception as e:
                    LOG.error(f"❌ Failed to register tool from {module_name}: {e}")
            else:
                missing = []
                if not hasattr(module, 'run'):
                    missing.append('run()')
                if not hasattr(module, 'spec'):
                    missing.append('spec()')
                LOG.warning(f"⚠️ {'Package' if ispkg else 'Module'} {module_name} missing {', '.join(missing)} functions")
    except ImportError as e:
        LOG.error(f"❌ Failed to import tools package: {e}")
    except Exception as e:
        LOG.error(f"❌ Unexpected error during tool discovery: {e}")
    new_count = len(registry)
    if new_count != old_count:
        LOG.info(f"🔄 Tool count changed: {old_count} → {new_count}")
        if new_count > old_count: LOG.info(f"🎉 {new_count - old_count} new tool(s) discovered!")
        elif new_count < old_count: LOG.info(f"🧹 {old_count - new_count} tool(s) removed")
    LOG.info(f"🔧 Tool discovery complete. Registered {new_count} tools: {list(registry.keys())}")


def should_reload(request: Request, auto_reload: bool, force_env: bool, current_registry_len: int) -> bool:
    if force_env or request.query_params.get('reload') == '1':
        LOG.info("🔄 Force reload requested")
        return True
    if current_registry_len == 0:
        LOG.info("🔄 No tools registered, reloading")
        return True
    if auto_reload:
        tools_info = get_tools_directory_info()
        current_mtime = tools_info["mtime"]
        current_file_set = tools_info["file_set"]
        global _tools_dir_mtime, _tools_file_set
        if current_mtime > _tools_dir_mtime:
            LOG.info(f"🔄 Tools directory modified (mtime: {_tools_dir_mtime} → {current_mtime})")
            return True
        if current_file_set != _tools_file_set:
            added = current_file_set - _tools_file_set
            removed = _tools_file_set - current_file_set
            if added:
                LOG.info(f"🔄 New tools detected: {added}")
                return True
            if removed:
                LOG.info(f"🔄 Tools removed: {removed}")
                return True
    return False


def tools_payload_etag(registry_snapshot: List[Dict[str, Any]]) -> str:
    payload = json.dumps(sanitize_for_json(registry_snapshot), separators=(",", ":"), ensure_ascii=False)
    return sha1(payload.encode('utf-8')).hexdigest()
