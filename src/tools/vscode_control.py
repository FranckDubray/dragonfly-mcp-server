"""
VS Code Control Tool - Contrôle VS Code en local via CLI et API
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Union
import json

_SPEC_DIR = Path(__file__).resolve().parent.parent / "tool_specs"


def _load_spec_override(name: str) -> Dict[str, Any] | None:
    try:
        p = _SPEC_DIR / f"{name}.json"
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


# Imports des modules de logique métier
from ._vscode_control.cli_ops import (
    open_file as cli_open_file,
    open_folder as cli_open_folder,
    diff_files as cli_diff_files,
    list_extensions as cli_list_extensions,
    install_extension as cli_install_extension,
    uninstall_extension as cli_uninstall_extension,
    get_version as cli_get_version,
    get_status as cli_get_status,
    execute_system_command as cli_execute_system_command,
)

from ._vscode_control.settings_ops import (
    get_settings,
    update_settings,
    list_common_settings,
)

from ._vscode_control.workspace_ops import (
    get_workspace_info,
    search_files,
    list_open_files,
    close_file,
    get_project_structure,
    read_file as workspace_read_file,
    write_file as workspace_write_file,
    append_to_file as workspace_append_to_file,
)

from ._vscode_control.diff_ops import (
    preview_file_changes as diff_preview_file_changes,
    apply_file_changes as diff_apply_file_changes,
    cancel_file_changes as diff_cancel_file_changes,
    list_pending_changes as diff_list_pending_changes,
)


def run(operation: str, **params) -> Union[Dict[str, Any], str]:
    """Point d'entrée principal pour toutes les opérations VS Code."""
    op = (operation or "").strip()
    
    # ===== Opérations CLI =====
    
    if op == "open_file":
        file_path = params.get("file_path")
        if not file_path:
            return {"error": "file_path is required"}
        
        return cli_open_file(
            file_path=file_path,
            new_window=params.get("new_window", False),
            wait=params.get("wait", False),
            goto_line=params.get("line_number"),
            goto_column=params.get("column_number")
        )
    
    if op == "open_folder":
        folder_path = params.get("folder_path")
        if not folder_path:
            return {"error": "folder_path is required"}
        
        return cli_open_folder(
            folder_path=folder_path,
            new_window=params.get("new_window", False),
            add_to_workspace=params.get("add_to_workspace", False)
        )
    
    if op == "diff_files":
        file_path_1 = params.get("file_path_1")
        file_path_2 = params.get("file_path_2")
        
        if not file_path_1 or not file_path_2:
            return {"error": "file_path_1 and file_path_2 are required"}
        
        return cli_diff_files(
            file_path_1=file_path_1,
            file_path_2=file_path_2,
            wait=params.get("wait", False)
        )
    
    if op == "goto_line":
        file_path = params.get("file_path")
        line_number = params.get("line_number")
        
        if not file_path or not line_number:
            return {"error": "file_path and line_number are required"}
        
        return cli_open_file(
            file_path=file_path,
            goto_line=line_number,
            goto_column=params.get("column_number")
        )
    
    if op == "list_extensions":
        return cli_list_extensions(
            show_categories=params.get("show_categories", False),
            include_disabled=params.get("include_disabled", False)
        )
    
    if op == "install_extension":
        extension_id = params.get("extension_id")
        if not extension_id:
            return {"error": "extension_id is required"}
        
        return cli_install_extension(extension_id)
    
    if op == "uninstall_extension":
        extension_id = params.get("extension_id")
        if not extension_id:
            return {"error": "extension_id is required"}
        
        return cli_uninstall_extension(extension_id)
    
    # ===== Opérations Settings =====
    
    if op == "get_settings":
        return get_settings(
            scope=params.get("scope", "user"),
            setting_key=params.get("setting_key")
        )
    
    if op == "update_settings":
        setting_key = params.get("setting_key")
        setting_value = params.get("setting_value")
        
        if not setting_key:
            return {"error": "setting_key is required"}
        
        if setting_value is None:
            return {"error": "setting_value is required"}
        
        return update_settings(
            setting_key=setting_key,
            setting_value=setting_value,
            scope=params.get("scope", "user")
        )
    
    # ===== Opérations Workspace =====
    
    if op == "get_workspace_info":
        return get_workspace_info()
    
    if op == "search_files":
        search_pattern = params.get("search_pattern")
        if not search_pattern:
            return {"error": "search_pattern is required"}
        
        return search_files(
            search_pattern=search_pattern,
            search_path=params.get("search_path")
        )
    
    if op == "list_open_files":
        return list_open_files()
    
    if op == "close_file":
        file_path = params.get("file_path")
        if not file_path:
            return {"error": "file_path is required"}
        
        return close_file(file_path)
    
    # ===== Opérations spéciales =====
    
    if op == "execute_command":
        # Note: Nécessite une extension VS Code pour exécuter des commandes arbitraires
        return {
            "success": False,
            "message": "execute_command requires VS Code API extension",
            "suggestion": "Use specific operations like 'open_file', 'open_folder', etc.",
            "command": params.get("command")
        }
    
    if op == "create_terminal":
        return {
            "success": False,
            "message": "create_terminal requires VS Code API extension",
            "suggestion": "Use VS Code's integrated terminal manually or install API extension"
        }
    
    if op == "run_in_terminal":
        return {
            "success": False,
            "message": "run_in_terminal requires VS Code API extension",
            "suggestion": "Use VS Code's integrated terminal manually or install API extension"
        }
    
    if op == "reload_window":
        return {
            "success": False,
            "message": "reload_window requires VS Code API extension",
            "suggestion": "Use 'Developer: Reload Window' command manually (Ctrl+R)"
        }
    
    # ===== Opérations utilitaires =====
    
    if op == "get_version":
        return cli_get_version()
    
    if op == "get_status":
        return cli_get_status()
    
    if op == "list_common_settings":
        return list_common_settings()
    
    if op == "get_project_structure":
        return get_project_structure(
            max_depth=params.get("max_depth", 3),
            include_hidden=params.get("include_hidden", False)
        )
    
    if op == "execute_system_command":
        command = params.get("command")
        if not command:
            return {"error": "command is required"}
        
        return cli_execute_system_command(
            command=command,
            timeout=params.get("timeout", 30)
        )
    
    if op == "read_file":
        file_path = params.get("file_path")
        if not file_path:
            return {"error": "file_path is required"}
        
        return workspace_read_file(
            file_path=file_path,
            encoding=params.get("encoding", "utf-8")
        )
    
    if op == "write_file":
        file_path = params.get("file_path")
        content = params.get("content")
        
        if not file_path:
            return {"error": "file_path is required"}
        
        if content is None:
            return {"error": "content is required"}
        
        return workspace_write_file(
            file_path=file_path,
            content=content,
            encoding=params.get("encoding", "utf-8"),
            create_dirs=params.get("create_dirs", True)
        )
    
    if op == "append_to_file":
        file_path = params.get("file_path")
        content = params.get("content")
        
        if not file_path:
            return {"error": "file_path is required"}
        
        if content is None:
            return {"error": "content is required"}
        
        return workspace_append_to_file(
            file_path=file_path,
            content=content,
            encoding=params.get("encoding", "utf-8")
        )
    
    # ===== Opérations Diff (Preview & Apply) =====
    
    if op == "preview_file_changes":
        file_path = params.get("file_path")
        new_content = params.get("content") or params.get("new_content")
        
        if not file_path:
            return {"error": "file_path is required"}
        
        if new_content is None:
            return {"error": "content (or new_content) is required"}
        
        return diff_preview_file_changes(
            file_path=file_path,
            new_content=new_content,
            operation=params.get("change_operation", "write"),
            encoding=params.get("encoding", "utf-8"),
            show_in_vscode=params.get("show_in_vscode", True)
        )
    
    if op == "apply_file_changes":
        change_id = params.get("change_id")
        
        if not change_id:
            return {"error": "change_id is required"}
        
        return diff_apply_file_changes(change_id)
    
    if op == "cancel_file_changes":
        change_id = params.get("change_id")
        
        if not change_id:
            return {"error": "change_id is required"}
        
        return diff_cancel_file_changes(change_id)
    
    if op == "list_pending_changes":
        return diff_list_pending_changes()
    
    # Opération inconnue
    return {
        "error": f"Unknown operation: {operation}",
        "available_operations": [
            "open_file", "open_folder", "diff_files", "goto_line",
            "list_extensions", "install_extension", "uninstall_extension",
            "get_settings", "update_settings",
            "get_workspace_info", "search_files",
            "get_version", "get_status", "list_common_settings", "get_project_structure",
            "execute_system_command", "read_file", "write_file", "append_to_file",
            "preview_file_changes", "apply_file_changes", "cancel_file_changes", "list_pending_changes"
        ]
    }


def spec() -> Dict[str, Any]:
    """Retourne la spécification de l'outil."""
    # Charger la spécification JSON canonique
    override = _load_spec_override("vscode_control")
    if override and isinstance(override, dict):
        return override
    
    # Fallback minimal si JSON manquant
    return {
        "type": "function",
        "function": {
            "name": "vscode_control",
            "displayName": "VS Code Control",
            "description": "Contrôle VS Code en local : fichiers, dossiers, extensions, paramètres.",
            "parameters": {
                "type": "object",
                "properties": {"operation": {"type": "string"}},
                "required": ["operation"],
                "additionalProperties": True
            }
        }
    }
