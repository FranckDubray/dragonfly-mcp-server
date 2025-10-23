"""
Diff Operations - Prévisualisation et application de modifications de fichiers
"""
from __future__ import annotations
import difflib
from pathlib import Path
from typing import Dict, Any, Optional


def generate_diff(old_content: str, new_content: str, file_path: str) -> str:
    """Génère un diff unifié entre deux contenus."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=''
    )
    
    return ''.join(diff)


def preview_file_changes(
    file_path: str,
    new_content: str,
    operation: str = "write",
    encoding: str = 'utf-8',
    show_in_vscode: bool = True
) -> Dict[str, Any]:
    """
    Prévisualise les modifications d'un fichier avant de les appliquer.
    
    Args:
        file_path: Chemin du fichier
        new_content: Nouveau contenu proposé
        operation: Type d'opération ('write' ou 'append')
        encoding: Encodage du fichier
        show_in_vscode: Afficher le diff visuellement dans VS Code
    
    Returns:
        Dict avec le diff et un change_id pour appliquer les modifications
    """
    try:
        path = Path(file_path)
        
        # Lire le contenu actuel si le fichier existe
        if path.exists():
            with open(path, 'r', encoding=encoding, errors='replace') as f:
                old_content = f.read()
            file_exists = True
        else:
            old_content = ""
            file_exists = False
        
        # Calculer le nouveau contenu selon l'opération
        if operation == "append" and file_exists:
            final_content = old_content + new_content
        else:
            final_content = new_content
        
        # Générer le diff
        diff_text = generate_diff(old_content, final_content, file_path)
        
        # Créer un change_id unique basé sur le hash du contenu
        import hashlib
        change_id = hashlib.sha256(
            f"{file_path}:{final_content}".encode()
        ).hexdigest()[:16]
        
        # Stocker le changement en attente
        store_pending_change(change_id, str(path.absolute()), final_content, encoding)
        
        # Statistiques
        old_lines = len(old_content.split('\n')) if old_content else 0
        new_lines = len(final_content.split('\n'))
        
        result = {
            "success": True,
            "file_path": str(path.absolute()),
            "file_exists": file_exists,
            "operation": operation,
            "change_id": change_id,
            "diff": diff_text,
            "stats": {
                "old_lines": old_lines,
                "new_lines": new_lines,
                "lines_added": new_lines - old_lines if file_exists else new_lines,
                "old_size": len(old_content),
                "new_size": len(final_content)
            },
            "message": "Preview ready. Use 'apply_file_changes' with this change_id to apply.",
            "instructions": {
                "to_apply": f"Use operation='apply_file_changes' with change_id='{change_id}'",
                "to_cancel": "Simply don't call apply_file_changes"
            }
        }
        
        # Afficher visuellement dans VS Code si demandé
        if show_in_vscode:
            vscode_result = show_diff_in_vscode(path, old_content, final_content, change_id)
            result["vscode_diff"] = vscode_result
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to preview changes: {str(e)}"
        }


def show_diff_in_vscode(original_path: Path, old_content: str, new_content: str, change_id: str) -> Dict[str, Any]:
    """
    Affiche le diff visuellement dans VS Code en créant des fichiers temporaires.
    """
    try:
        import tempfile
        import subprocess
        import platform
        
        # Créer un dossier temporaire pour les fichiers de diff
        temp_dir = Path(tempfile.gettempdir()) / "vscode_diff_preview"
        temp_dir.mkdir(exist_ok=True)
        
        # Noms des fichiers temporaires
        original_name = original_path.name
        old_file = temp_dir / f"{change_id}_BEFORE_{original_name}"
        new_file = temp_dir / f"{change_id}_AFTER_{original_name}"
        
        # Écrire les contenus
        with open(old_file, 'w', encoding='utf-8') as f:
            f.write(old_content if old_content else "# Fichier vide (nouveau fichier)\n")
        
        with open(new_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Trouver l'exécutable code
        code_exe = _find_code_executable()
        
        # Ouvrir le diff dans VS Code
        cmd = [code_exe, '--diff', str(old_file), str(new_file)]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return {
            "success": result.returncode == 0,
            "message": "Diff opened in VS Code",
            "temp_files": {
                "before": str(old_file),
                "after": str(new_file)
            },
            "instruction": f"Review the diff in VS Code, then use apply_file_changes('{change_id}') to apply or cancel_file_changes('{change_id}') to cancel"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to show diff in VS Code: {str(e)}",
            "fallback": "Use the 'diff' field in the response to see changes"
        }


def _find_code_executable() -> str:
    """Trouve l'exécutable 'code' de VS Code."""
    import os
    import platform
    
    # Essayer 'code' directement (dans PATH)
    try:
        result = subprocess.run(['code', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return 'code'
    except:
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
    
    raise FileNotFoundError("VS Code CLI 'code' not found")


# Stockage temporaire des modifications en attente
_pending_changes: Dict[str, Dict[str, Any]] = {}


def store_pending_change(change_id: str, file_path: str, content: str, encoding: str):
    """Stocke une modification en attente."""
    _pending_changes[change_id] = {
        "file_path": file_path,
        "content": content,
        "encoding": encoding
    }


def apply_file_changes(change_id: str, close_diff: bool = True) -> Dict[str, Any]:
    """
    Applique les modifications prévisualisées après confirmation de l'utilisateur.
    
    Args:
        change_id: ID de la modification à appliquer
        close_diff: Fermer les fichiers de diff dans VS Code après application
    
    Returns:
        Dict avec le résultat de l'application
    """
    if change_id not in _pending_changes:
        return {
            "success": False,
            "error": f"Change ID '{change_id}' not found or expired",
            "suggestion": "Use 'preview_file_changes' first to generate a change_id"
        }
    
    try:
        change = _pending_changes[change_id]
        file_path = change["file_path"]
        content = change["content"]
        encoding = change["encoding"]
        
        path = Path(file_path)
        
        # Créer les dossiers parents si nécessaire
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        
        # Écrire le fichier
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        
        # Obtenir les infos du fichier
        stats = path.stat()
        
        result = {
            "success": True,
            "file_path": str(path.absolute()),
            "size": stats.st_size,
            "lines": len(content.split('\n')),
            "encoding": encoding,
            "message": f"Changes applied successfully to: {path.name}"
        }
        
        # Fermer les fichiers de diff si demandé et ouvrir le fichier réel
        if close_diff:
            cleanup_result = cleanup_diff_files(change_id, open_real_file=str(path.absolute()))
            result["cleanup"] = cleanup_result
        
        # Nettoyer le changement en attente
        del _pending_changes[change_id]
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to apply changes: {str(e)}"
        }


def cancel_file_changes(change_id: str, close_diff: bool = True) -> Dict[str, Any]:
    """
    Annule une modification en attente.
    
    Args:
        change_id: ID de la modification à annuler
        close_diff: Fermer les fichiers de diff dans VS Code après annulation
    
    Returns:
        Dict avec le résultat de l'annulation
    """
    if change_id not in _pending_changes:
        return {
            "success": False,
            "error": f"Change ID '{change_id}' not found"
        }
    
    change = _pending_changes[change_id]
    file_path = change["file_path"]
    
    result = {
        "success": True,
        "message": f"Changes cancelled for: {file_path}",
        "file_path": file_path
    }
    
    # Fermer les fichiers de diff si demandé
    if close_diff:
        cleanup_result = cleanup_diff_files(change_id)
        result["cleanup"] = cleanup_result
    
    del _pending_changes[change_id]
    
    return result


def cleanup_diff_files(change_id: str, open_real_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Nettoie les fichiers temporaires de diff et les ferme dans VS Code.
    
    Args:
        change_id: ID du changement dont il faut nettoyer les fichiers
        open_real_file: Chemin du fichier réel à ouvrir pour remplacer la vue diff
    
    Returns:
        Dict avec le résultat du nettoyage
    """
    try:
        import tempfile
        import subprocess
        import time
        
        temp_dir = Path(tempfile.gettempdir()) / "vscode_diff_preview"
        
        # Trouver les fichiers temporaires pour ce change_id
        before_file = None
        after_file = None
        
        if temp_dir.exists():
            for file in temp_dir.glob(f"{change_id}_*"):
                if "_BEFORE_" in file.name:
                    before_file = file
                elif "_AFTER_" in file.name:
                    after_file = file
        
        closed_files = []
        
        # Supprimer les fichiers temporaires
        if before_file or after_file:
            try:
                for file in [before_file, after_file]:
                    if file and file.exists():
                        file.unlink()
                        closed_files.append(str(file))
                
                # Attendre un peu pour que VS Code détecte la suppression
                time.sleep(0.5)
                
                # Si un fichier réel est fourni, l'ouvrir pour remplacer la vue diff
                if open_real_file:
                    try:
                        code_exe = _find_code_executable()
                        # Ouvrir le fichier réel (cela remplacera la vue diff)
                        subprocess.run(
                            [code_exe, '--reuse-window', open_real_file],
                            capture_output=True,
                            timeout=5
                        )
                    except Exception as e:
                        pass  # Ignorer les erreurs d'ouverture
                
            except Exception as e:
                pass  # Ignorer les erreurs de fermeture
        
        return {
            "success": True,
            "message": "Diff files cleaned up" + (" and real file opened" if open_real_file else ""),
            "files_removed": closed_files,
            "count": len(closed_files),
            "real_file_opened": open_real_file if open_real_file else None
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to cleanup diff files: {str(e)}"
        }


def list_pending_changes() -> Dict[str, Any]:
    """Liste toutes les modifications en attente."""
    if not _pending_changes:
        return {
            "success": True,
            "pending_changes": [],
            "count": 0,
            "message": "No pending changes"
        }
    
    changes = []
    for change_id, change in _pending_changes.items():
        changes.append({
            "change_id": change_id,
            "file_path": change["file_path"],
            "content_size": len(change["content"])
        })
    
    return {
        "success": True,
        "pending_changes": changes,
        "count": len(changes),
        "message": f"{len(changes)} pending change(s)"
    }
