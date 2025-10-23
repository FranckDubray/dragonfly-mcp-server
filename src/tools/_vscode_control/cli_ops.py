"""
VS Code CLI Operations - Interaction via la ligne de commande 'code'
"""
from __future__ import annotations
import subprocess
import json
import os
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional


def _find_code_executable() -> str:
    """Trouve l'exécutable 'code' de VS Code."""
    # Essayer 'code' directement (dans PATH)
    try:
        result = subprocess.run(['code', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return 'code'
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Chemins spécifiques selon l'OS
    system = platform.system()
    possible_paths = []
    
    if system == 'Windows':
        possible_paths = [
            r'C:\Program Files\Microsoft VS Code\bin\code.cmd',
            r'C:\Program Files (x86)\Microsoft VS Code\bin\code.cmd',
            os.path.expandvars(r'%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd'),
        ]
    elif system == 'Darwin':  # macOS
        possible_paths = [
            '/usr/local/bin/code',
            '/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code',
        ]
    else:  # Linux
        possible_paths = [
            '/usr/bin/code',
            '/usr/local/bin/code',
            os.path.expanduser('~/.local/bin/code'),
        ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError("VS Code CLI 'code' not found. Make sure VS Code is installed and 'code' is in PATH.")


def _run_code_command(args: List[str], timeout: int = 30) -> Dict[str, Any]:
    """Exécute une commande 'code' et retourne le résultat."""
    try:
        code_exe = _find_code_executable()
        cmd = [code_exe] + args
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "command": ' '.join(cmd)
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Command timed out after {timeout}s",
            "command": ' '.join(args)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": ' '.join(args)
        }


def open_file(file_path: str, new_window: bool = False, wait: bool = False, 
              goto_line: Optional[int] = None, goto_column: Optional[int] = None) -> Dict[str, Any]:
    """Ouvre un fichier dans VS Code."""
    args = []
    
    if new_window:
        args.append('--new-window')
    
    if wait:
        args.append('--wait')
    
    # Construire le chemin avec ligne:colonne si spécifié
    path = str(Path(file_path).resolve())
    if goto_line:
        path += f":{goto_line}"
        if goto_column:
            path += f":{goto_column}"
    
    args.append('--goto')
    args.append(path)
    
    result = _run_code_command(args)
    
    if result["success"]:
        result["message"] = f"File opened: {file_path}"
        if goto_line:
            result["message"] += f" at line {goto_line}"
    
    return result


def open_folder(folder_path: str, new_window: bool = False, add_to_workspace: bool = False) -> Dict[str, Any]:
    """Ouvre un dossier dans VS Code."""
    args = []
    
    if new_window:
        args.append('--new-window')
    elif add_to_workspace:
        args.append('--add')
    
    path = str(Path(folder_path).resolve())
    args.append(path)
    
    result = _run_code_command(args)
    
    if result["success"]:
        action = "added to workspace" if add_to_workspace else "opened"
        result["message"] = f"Folder {action}: {folder_path}"
    
    return result


def diff_files(file_path_1: str, file_path_2: str, wait: bool = False) -> Dict[str, Any]:
    """Compare deux fichiers dans VS Code."""
    args = ['--diff']
    
    if wait:
        args.append('--wait')
    
    path1 = str(Path(file_path_1).resolve())
    path2 = str(Path(file_path_2).resolve())
    
    args.extend([path1, path2])
    
    result = _run_code_command(args)
    
    if result["success"]:
        result["message"] = f"Comparing: {file_path_1} <-> {file_path_2}"
    
    return result


def list_extensions(show_categories: bool = False, include_disabled: bool = False) -> Dict[str, Any]:
    """Liste les extensions installées."""
    args = ['--list-extensions']
    
    if show_categories:
        args.append('--category')
    
    result = _run_code_command(args)
    
    if result["success"]:
        extensions = [ext for ext in result["stdout"].split('\n') if ext.strip()]
        result["extensions"] = extensions
        result["count"] = len(extensions)
        result["message"] = f"Found {len(extensions)} extension(s)"
    
    return result


def install_extension(extension_id: str) -> Dict[str, Any]:
    """Installe une extension."""
    args = ['--install-extension', extension_id]
    
    result = _run_code_command(args, timeout=120)  # Plus de temps pour l'installation
    
    if result["success"]:
        result["message"] = f"Extension installed: {extension_id}"
    
    return result


def uninstall_extension(extension_id: str) -> Dict[str, Any]:
    """Désinstalle une extension."""
    args = ['--uninstall-extension', extension_id]
    
    result = _run_code_command(args, timeout=60)
    
    if result["success"]:
        result["message"] = f"Extension uninstalled: {extension_id}"
    
    return result


def get_version() -> Dict[str, Any]:
    """Récupère la version de VS Code."""
    result = _run_code_command(['--version'])
    
    if result["success"]:
        lines = result["stdout"].split('\n')
        if len(lines) >= 3:
            result["version"] = lines[0]
            result["commit"] = lines[1]
            result["architecture"] = lines[2]
    
    return result


def reload_window() -> Dict[str, Any]:
    """Recharge la fenêtre VS Code (via commande)."""
    # Note: Cette opération nécessite une extension ou l'API REST
    # Pour l'instant, on retourne une indication
    return {
        "success": False,
        "message": "reload_window requires VS Code API extension (not available via CLI)",
        "suggestion": "Use 'Developer: Reload Window' command manually or install API extension"
    }


def get_status() -> Dict[str, Any]:
    """Récupère le statut de VS Code."""
    args = ['--status']
    result = _run_code_command(args)
    
    if result["success"]:
        result["message"] = "VS Code status retrieved"
    
    return result


def execute_system_command(command: str, timeout: int = 30) -> Dict[str, Any]:
    """Exécute une commande système arbitraire."""
    try:
        import shlex
        
        # Parser la commande de manière sécurisée
        if platform.system() == 'Windows':
            # Sur Windows, on n'utilise pas shlex
            cmd_parts = command.split()
        else:
            cmd_parts = shlex.split(command)
        
        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace',
            shell=False  # Important pour la sécurité
        )
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "command": command,
            "message": f"Command executed: {command}"
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Command timed out after {timeout}s",
            "command": command
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"Command not found: {cmd_parts[0] if cmd_parts else command}",
            "command": command,
            "suggestion": "Make sure the command is installed and in PATH"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": command
        }
