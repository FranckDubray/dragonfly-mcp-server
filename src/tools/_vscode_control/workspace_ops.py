"""
VS Code Workspace Operations - Gestion des workspaces et recherche de fichiers
"""
from __future__ import annotations
import json
import os
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional


def get_workspace_info() -> Dict[str, Any]:
    """Récupère les informations sur le workspace actuel."""
    cwd = Path.cwd()
    
    # Chercher un fichier .code-workspace
    workspace_files = list(cwd.glob("*.code-workspace"))
    
    # Chercher un dossier .vscode
    vscode_dir = cwd / ".vscode"
    
    result = {
        "success": True,
        "current_directory": str(cwd),
        "has_vscode_folder": vscode_dir.exists(),
    }
    
    if workspace_files:
        result["workspace_files"] = [str(f.name) for f in workspace_files]
        result["workspace_count"] = len(workspace_files)
        
        # Lire le premier workspace file
        try:
            with open(workspace_files[0], 'r', encoding='utf-8') as f:
                workspace_data = json.load(f)
                result["workspace_data"] = workspace_data
        except Exception as e:
            result["workspace_read_error"] = str(e)
    else:
        result["workspace_files"] = []
        result["workspace_count"] = 0
    
    # Lister les fichiers dans .vscode
    if vscode_dir.exists():
        vscode_files = [f.name for f in vscode_dir.iterdir() if f.is_file()]
        result["vscode_files"] = vscode_files
    
    result["message"] = f"Workspace info for: {cwd.name}"
    
    return result


def search_files(search_pattern: str, search_path: Optional[str] = None, 
                 max_results: int = 100) -> Dict[str, Any]:
    """Recherche des fichiers selon un pattern glob."""
    if not search_pattern:
        return {
            "success": False,
            "error": "search_pattern is required"
        }
    
    # Déterminer le chemin de recherche
    if search_path:
        base_path = Path(search_path)
        if not base_path.exists():
            return {
                "success": False,
                "error": f"Search path does not exist: {search_path}"
            }
    else:
        base_path = Path.cwd()
    
    try:
        # Recherche récursive avec glob
        pattern = str(base_path / "**" / search_pattern)
        matches = []
        
        for file_path in glob.glob(pattern, recursive=True):
            path_obj = Path(file_path)
            if path_obj.is_file():
                matches.append({
                    "path": str(path_obj),
                    "name": path_obj.name,
                    "size": path_obj.stat().st_size,
                    "relative_path": str(path_obj.relative_to(base_path))
                })
                
                if len(matches) >= max_results:
                    break
        
        return {
            "success": True,
            "pattern": search_pattern,
            "search_path": str(base_path),
            "matches": matches,
            "count": len(matches),
            "truncated": len(matches) >= max_results,
            "message": f"Found {len(matches)} file(s) matching '{search_pattern}'"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }


def list_open_files() -> Dict[str, Any]:
    """Liste les fichiers ouverts (simulation - nécessite extension)."""
    # Note: Cette fonctionnalité nécessite une extension VS Code
    # Pour l'instant, on retourne une indication
    return {
        "success": False,
        "message": "list_open_files requires VS Code API extension",
        "suggestion": "This feature needs a VS Code extension to access the editor state",
        "alternative": "Use 'get_workspace_info' to see workspace structure"
    }


def close_file(file_path: str) -> Dict[str, Any]:
    """Ferme un fichier (simulation - nécessite extension)."""
    # Note: Cette fonctionnalité nécessite une extension VS Code
    return {
        "success": False,
        "message": "close_file requires VS Code API extension",
        "suggestion": "This feature needs a VS Code extension to control the editor",
        "file_path": file_path
    }


def create_workspace_file(workspace_name: str, folders: List[str], 
                         settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Crée un fichier .code-workspace."""
    if not workspace_name:
        return {
            "success": False,
            "error": "workspace_name is required"
        }
    
    if not folders:
        return {
            "success": False,
            "error": "At least one folder is required"
        }
    
    # Construire la structure du workspace
    workspace_data = {
        "folders": [{"path": folder} for folder in folders]
    }
    
    if settings:
        workspace_data["settings"] = settings
    
    # Nom du fichier
    workspace_file = Path.cwd() / f"{workspace_name}.code-workspace"
    
    try:
        with open(workspace_file, 'w', encoding='utf-8') as f:
            json.dump(workspace_data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "workspace_file": str(workspace_file),
            "folders": folders,
            "message": f"Workspace file created: {workspace_file.name}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create workspace file: {str(e)}"
        }


def read_file(file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
    """Lit le contenu d'un fichier."""
    try:
        path = Path(file_path)
        
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        if not path.is_file():
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}"
            }
        
        # Lire le fichier
        with open(path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        
        # Obtenir les infos du fichier
        stats = path.stat()
        
        return {
            "success": True,
            "file_path": str(path.absolute()),
            "content": content,
            "size": stats.st_size,
            "lines": len(content.split('\n')),
            "encoding": encoding,
            "message": f"File read successfully: {path.name}"
        }
    
    except UnicodeDecodeError:
        return {
            "success": False,
            "error": f"Unable to decode file with encoding '{encoding}'",
            "suggestion": "Try a different encoding or this might be a binary file"
        }
    except PermissionError:
        return {
            "success": False,
            "error": f"Permission denied: {file_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read file: {str(e)}"
        }


def write_file(file_path: str, content: str, encoding: str = 'utf-8', create_dirs: bool = True) -> Dict[str, Any]:
    """Écrit du contenu dans un fichier."""
    try:
        path = Path(file_path)
        
        # Créer les dossiers parents si nécessaire
        if create_dirs and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        
        # Écrire le fichier
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        
        # Obtenir les infos du fichier
        stats = path.stat()
        
        return {
            "success": True,
            "file_path": str(path.absolute()),
            "size": stats.st_size,
            "lines": len(content.split('\n')),
            "encoding": encoding,
            "message": f"File written successfully: {path.name}"
        }
    
    except PermissionError:
        return {
            "success": False,
            "error": f"Permission denied: {file_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to write file: {str(e)}"
        }


def append_to_file(file_path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
    """Ajoute du contenu à la fin d'un fichier."""
    try:
        path = Path(file_path)
        
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "suggestion": "Use write_file to create a new file"
            }
        
        # Ajouter le contenu
        with open(path, 'a', encoding=encoding) as f:
            f.write(content)
        
        # Obtenir les infos du fichier
        stats = path.stat()
        
        return {
            "success": True,
            "file_path": str(path.absolute()),
            "size": stats.st_size,
            "encoding": encoding,
            "message": f"Content appended to: {path.name}"
        }
    
    except PermissionError:
        return {
            "success": False,
            "error": f"Permission denied: {file_path}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to append to file: {str(e)}"
        }


def get_project_structure(max_depth: int = 3, include_hidden: bool = False) -> Dict[str, Any]:
    """Récupère la structure du projet sous forme d'arbre."""
    cwd = Path.cwd()
    
    def build_tree(path: Path, current_depth: int = 0) -> Dict[str, Any]:
        """Construit récursivement l'arbre des fichiers."""
        if current_depth >= max_depth:
            return None
        
        tree = {
            "name": path.name,
            "type": "directory" if path.is_dir() else "file",
            "path": str(path.relative_to(cwd))
        }
        
        if path.is_dir():
            children = []
            try:
                for item in sorted(path.iterdir()):
                    # Ignorer les fichiers cachés si demandé
                    if not include_hidden and item.name.startswith('.'):
                        continue
                    
                    child = build_tree(item, current_depth + 1)
                    if child:
                        children.append(child)
                
                if children:
                    tree["children"] = children
                    tree["child_count"] = len(children)
            except PermissionError:
                tree["error"] = "Permission denied"
        else:
            try:
                tree["size"] = path.stat().st_size
            except:
                pass
        
        return tree
    
    try:
        structure = build_tree(cwd)
        
        return {
            "success": True,
            "root": str(cwd),
            "max_depth": max_depth,
            "structure": structure,
            "message": f"Project structure for: {cwd.name}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to build project structure: {str(e)}"
        }
