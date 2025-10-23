"""
VS Code Settings Operations - Gestion des paramètres utilisateur et workspace
"""
from __future__ import annotations
import json
import os
import platform
from pathlib import Path
from typing import Dict, Any, Optional


def _get_settings_path(scope: str = "user") -> Path:
    """Retourne le chemin du fichier settings.json selon le scope."""
    system = platform.system()
    
    if scope == "user":
        if system == "Windows":
            base = Path(os.getenv('APPDATA', ''))
            return base / "Code" / "User" / "settings.json"
        elif system == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "Code" / "User" / "settings.json"
        else:  # Linux
            return Path.home() / ".config" / "Code" / "User" / "settings.json"
    else:  # workspace
        # Pour workspace, on cherche dans le dossier courant
        workspace_settings = Path.cwd() / ".vscode" / "settings.json"
        return workspace_settings


def _read_settings(scope: str = "user") -> Dict[str, Any]:
    """Lit le fichier settings.json."""
    settings_path = _get_settings_path(scope)
    
    if not settings_path.exists():
        return {}
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            # Supporter les commentaires JSON (jsonc)
            content = f.read()
            # Supprimer les commentaires simples
            lines = []
            for line in content.split('\n'):
                # Ignorer les lignes de commentaires
                stripped = line.strip()
                if not stripped.startswith('//'):
                    lines.append(line)
            clean_content = '\n'.join(lines)
            return json.loads(clean_content)
    except Exception as e:
        return {"error": f"Failed to read settings: {str(e)}"}


def _write_settings(settings: Dict[str, Any], scope: str = "user") -> Dict[str, Any]:
    """Écrit dans le fichier settings.json."""
    settings_path = _get_settings_path(scope)
    
    try:
        # Créer le dossier si nécessaire
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "message": f"Settings saved to {scope} scope",
            "path": str(settings_path)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to write settings: {str(e)}"
        }


def get_settings(scope: str = "user", setting_key: Optional[str] = None) -> Dict[str, Any]:
    """Récupère les paramètres VS Code."""
    settings = _read_settings(scope)
    
    if "error" in settings:
        return settings
    
    result = {
        "success": True,
        "scope": scope,
        "path": str(_get_settings_path(scope))
    }
    
    if setting_key:
        # Récupérer une clé spécifique
        value = settings.get(setting_key)
        if value is not None:
            result["setting"] = {setting_key: value}
            result["message"] = f"Setting '{setting_key}' retrieved"
        else:
            result["success"] = False
            result["error"] = f"Setting '{setting_key}' not found"
    else:
        # Récupérer tous les paramètres
        result["settings"] = settings
        result["count"] = len(settings)
        result["message"] = f"Retrieved {len(settings)} setting(s)"
    
    return result


def update_settings(setting_key: str, setting_value: Any, scope: str = "user") -> Dict[str, Any]:
    """Met à jour un paramètre VS Code."""
    if not setting_key:
        return {
            "success": False,
            "error": "setting_key is required"
        }
    
    # Lire les paramètres existants
    settings = _read_settings(scope)
    
    if "error" in settings:
        # Si le fichier n'existe pas, créer un nouveau dict
        settings = {}
    
    # Mettre à jour la clé
    old_value = settings.get(setting_key)
    settings[setting_key] = setting_value
    
    # Sauvegarder
    result = _write_settings(settings, scope)
    
    if result["success"]:
        result["setting"] = {setting_key: setting_value}
        if old_value is not None:
            result["old_value"] = old_value
            result["message"] = f"Setting '{setting_key}' updated"
        else:
            result["message"] = f"Setting '{setting_key}' created"
    
    return result


def delete_setting(setting_key: str, scope: str = "user") -> Dict[str, Any]:
    """Supprime un paramètre VS Code."""
    if not setting_key:
        return {
            "success": False,
            "error": "setting_key is required"
        }
    
    settings = _read_settings(scope)
    
    if "error" in settings:
        return settings
    
    if setting_key not in settings:
        return {
            "success": False,
            "error": f"Setting '{setting_key}' not found"
        }
    
    old_value = settings.pop(setting_key)
    result = _write_settings(settings, scope)
    
    if result["success"]:
        result["deleted"] = {setting_key: old_value}
        result["message"] = f"Setting '{setting_key}' deleted"
    
    return result


def list_common_settings() -> Dict[str, Any]:
    """Liste les paramètres VS Code les plus courants avec leurs descriptions."""
    common_settings = {
        "editor.fontSize": "Taille de la police de l'éditeur",
        "editor.fontFamily": "Famille de police de l'éditeur",
        "editor.tabSize": "Nombre d'espaces pour une tabulation",
        "editor.wordWrap": "Retour à la ligne automatique",
        "editor.minimap.enabled": "Afficher la minimap",
        "editor.formatOnSave": "Formater automatiquement à la sauvegarde",
        "files.autoSave": "Sauvegarde automatique des fichiers",
        "workbench.colorTheme": "Thème de couleur",
        "workbench.iconTheme": "Thème d'icônes",
        "terminal.integrated.fontSize": "Taille de police du terminal",
        "terminal.integrated.shell.windows": "Shell par défaut (Windows)",
        "terminal.integrated.shell.linux": "Shell par défaut (Linux)",
        "terminal.integrated.shell.osx": "Shell par défaut (macOS)",
        "python.defaultInterpreterPath": "Chemin de l'interpréteur Python",
        "git.autofetch": "Récupération automatique Git",
        "git.confirmSync": "Confirmer avant sync Git",
    }
    
    return {
        "success": True,
        "settings": common_settings,
        "count": len(common_settings),
        "message": f"Listed {len(common_settings)} common settings"
    }
