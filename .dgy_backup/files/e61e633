
"""
Git Tool - Complete GitHub API + Local Git operations
"""
import os
import base64
import requests
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import json

try:
    from config import find_project_root
except ImportError:
    find_project_root = lambda: Path.cwd()

# Import helpers
from ._git.local_ops import GitLocalOps

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

# -----------------------------
# Chroot helpers (MODIFIED TO ACCESS PROJECT ROOT)
# -----------------------------

def _chroot_base() -> Path:
    return find_project_root().resolve()  # removed /clone


def _resolve_in_chroot(rel_path: Optional[str]) -> Path:
    base = _chroot_base()
    if not rel_path or str(rel_path).strip() in ("", ".", "/"):
        return base
    p = (base / rel_path).resolve()
    # Prevent path escape
    if not str(p).startswith(str(base)):
        raise ValueError(f"Path escapes chroot: {rel_path}")
    return p


def _read_file_in_chroot(local_path: str) -> str:
    p = _resolve_in_chroot(local_path)
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {local_path}")
    return p.read_text(encoding="utf-8")


def _sanitize_repo_dir(param_repo_dir: Optional[str]) -> Path:
    try:
        return _resolve_in_chroot(param_repo_dir)
    except Exception:
        # Fallback to chroot base on error
        return _chroot_base()


def _sanitize_paths_within_repo(repo_dir: Path, paths: List[str]) -> List[str]:
    clean: List[str] = []
    for p in paths:
        rp = (repo_dir / p).resolve()
        if not str(rp).startswith(str(repo_dir)):
            # skip paths escaping repo_dir
            continue
        # use relative path for git commands
        clean.append(os.path.relpath(rp, start=repo_dir))
    return clean


def run(operation: str, **params) -> Union[Dict[str, Any], str]:
    op = operation.strip() if operation else ""
    
    # GitHub API operations
    if op == "create_repo":
        name = params.get('name')
        if not name: return {"error": "repository name required"}
        data = {
            "name": name,
            "description": params.get('description', ''),
            "private": params.get('private', False)
        }
        return _github_api_request("POST", "/user/repos", data)
    
    if op == "get_user":
        username = params.get('username')
        if not username: return {"error": "username required"}
        return _github_api_request("GET", f"/users/{username}")
    
    if op == "list_repos":
        username = params.get('username')
        if username:
            return _github_api_request("GET", f"/users/{username}/repos")
        return _github_api_request("GET", "/user/repos")
    
    if op == "add_file":
        owner = params.get('owner')
        repo = params.get('repo')
        file_path = params.get('file_path')  # local path (inside project root)
        repo_path = params.get('repo_path')
        message = params.get('message', f"Add {repo_path}")
        branch = params.get('branch', 'main')
        
        if not all([owner, repo, file_path, repo_path]):
            return {"error": "owner, repo, file_path, and repo_path required"}
        
        try:
            content = _read_file_in_chroot(file_path)
        except Exception as e:
            return {"error": f"Error reading file: {e}"}
        
        return _create_or_update_file(owner, repo, repo_path, content, message, branch)
    
    if op == "add_multiple_files":
        owner = params.get('owner')
        repo = params.get('repo')
        files = params.get('files', [])
        message = params.get('message', "Add multiple files")
        branch = params.get('branch', 'main')
        
        if not all([owner, repo, files]):
            return {"error": "owner, repo, and files list required"}
        
        results = []
        for file_info in files:
            if isinstance(file_info, dict):
                local_path = file_info.get('local_path')
                repo_path = file_info.get('repo_path')
                if not local_path or not repo_path:
                    results.append({"error": f"Missing local_path or repo_path in {file_info}"})
                    continue
                
                try:
                    content = _read_file_in_chroot(local_path)
                except Exception as e:
                    results.append({"error": str(e), "file": local_path})
                    continue
                
                result = _create_or_update_file(owner, repo, repo_path, content, f"{message} - {repo_path}", branch)
                results.append({"file": repo_path, "result": result})
        
        return {"results": results, "total": len(files), "processed": len(results)}
    
    if op == "delete_file":
        owner = params.get('owner')
        repo = params.get('repo')
        file_path = params.get('file_path')
        message = params.get('message', f"Delete {file_path}")
        branch = params.get('branch', 'main')
        
        if not all([owner, repo, file_path]):
            return {"error": "owner, repo, and file_path required"}
        
        return _delete_file_from_repo(owner, repo, file_path, message, branch)
    
    if op == "delete_multiple_files":
        owner = params.get('owner')
        repo = params.get('repo')
        files = params.get('files', [])
        message = params.get('message', "Delete multiple files")
        branch = params.get('branch', 'main')
        
        if not all([owner, repo, files]):
            return {"error": "owner, repo, and files list required"}
        
        results = []
        for file_path in files:
            if isinstance(file_path, str):
                path = file_path
            elif isinstance(file_path, dict) and 'repo_path' in file_path:
                path = file_path['repo_path']
            else:
                results.append({"error": f"Invalid file entry: {file_path}"})
                continue
            
            result = _delete_file_from_repo(owner, repo, path, f"{message} - {path}", branch)
            results.append({"file": path, "result": result})
        
        return {"results": results, "total": len(files), "processed": len(results)}
    
    if op == "get_repo_contents":
        owner = params.get('owner')
        repo = params.get('repo')
        path = params.get('path', '')
        branch = params.get('branch')
        
        if not all([owner, repo]):
            return {"error": "owner and repo required"}
        
        endpoint = f"/repos/{owner}/{repo}/contents"
        if path:
            endpoint += f"/{path}"
        
        params_q = {"ref": branch} if branch else None
        return _github_api_request("GET", endpoint, params=params_q)
    
    if op == "create_branch":
        owner = params.get('owner')
        repo = params.get('repo')
        branch_name = params.get('branch_name')
        from_branch = params.get('from_branch', 'main')
        
        if not all([owner, repo, branch_name]):
            return {"error": "owner, repo, and branch_name required"}
        
        # Get SHA of from_branch
        ref_response = _github_api_request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{from_branch}")
        if "object" not in ref_response:
            return {"error": f"Could not get SHA for branch {from_branch}", "details": ref_response}
        
        sha = ref_response["object"]["sha"]
        data = {"ref": f"refs/heads/{branch_name}", "sha": sha}
        return _github_api_request("POST", f"/repos/{owner}/{repo}/git/refs", data)
    
    if op == "get_commits":
        owner = params.get('owner')
        repo = params.get('repo')
        branch = params.get('branch', 'main')
        count = params.get('count', 5)
        
        if not all([owner, repo]):
            return {"error": "owner and repo required"}
        
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/commits",
            params={"sha": branch, "per_page": count},
            headers=_get_github_headers()
        )
        
        if response.status_code >= 400:
            return {"error": f"GitHub API error {response.status_code}: {response.text}"}
        
        commits = response.json()
        return {
            "commits": [
                {
                    "sha": c.get("sha", "")[:7],
                    "message": c.get("commit", {}).get("message", ""),
                    "author": c.get("commit", {}).get("author", {}).get("name", ""),
                    "date": c.get("commit", {}).get("author", {}).get("date", ""),
                }
                for c in commits
            ]
        }
    
    if op == "diff":
        owner = params.get('owner')
        repo = params.get('repo')
        base = params.get('base', 'main')
        head = params.get('head')
        
        if not all([owner, repo, head]):
            return {"error": "owner, repo, and head required for diff"}
        
        return _github_api_request("GET", f"/repos/{owner}/{repo}/compare/{base}...{head}")
    
    # MERGE - Smart routing: GitHub API if owner+repo, else local
    if op == "merge":
        owner = params.get('owner')
        repo = params.get('repo')
        
        if owner and repo:
            # GitHub merge via API
            base = params.get('base')
            head = params.get('head')
            commit_title = params.get('commit_title')
            commit_message = params.get('message') or params.get('commit_message')
            
            if not all([base, head]):
                return {"error": "base and head required for GitHub merge"}
            
            data = {"base": base, "head": head}
            if commit_title:
                data["commit_title"] = commit_title
            if commit_message:
                data["commit_message"] = commit_message
            
            return _github_api_request("POST", f"/repos/{owner}/{repo}/merges", data)
        else:
            # Local merge via git CLI (chrooted)
            local_ops = GitLocalOps()
            repo_dir = _sanitize_repo_dir(params.get('repo_dir'))
            source = params.get('source') or params.get('head') or params.get('from_branch')
            
            if not source:
                return {"error": "source (branch to merge) required for local merge"}
            
            return local_ops.handle_merge(repo_dir, source, **params)
    
    # Local Git operations (within project root now)
    if op in ["status", "branch_create", "checkout", "add_paths", "commit_all", "push"]:
        local_ops = GitLocalOps()
        repo_dir = _sanitize_repo_dir(params.get('repo_dir'))
        
        if op == "status":
            return local_ops.handle_status(repo_dir)
        elif op == "branch_create":
            branch_name = params.get('branch_name')
            if not branch_name:
                return {"error": "branch_name required"}
            return local_ops.handle_branch_create(repo_dir, branch_name, params.get('from_branch'))
        elif op == "checkout":
            branch = params.get('branch')
            if not branch:
                return {"error": "branch required"}
            return local_ops.handle_checkout(repo_dir, branch)
        elif op == "add_paths":
            paths = params.get('paths', [])
            if not paths:
                return {"error": "paths (list) required"}
            paths = _sanitize_paths_within_repo(repo_dir, paths)
            if not paths:
                return {"error": "no valid paths inside repo_dir"}
            return local_ops.handle_add_paths(repo_dir, paths)
        elif op == "commit_all":
            message = params.get('message')
            if not message:
                return {"error": "message required"}
            return local_ops.handle_commit_all(repo_dir, message)
        elif op == "push":
            branch = params.get('branch')
            if not branch:
                return {"error": "branch required"}
            return local_ops.handle_push(repo_dir, branch, params.get('remote', "origin"), params.get('set_upstream', True))
    
    if op == "clone":
        repo_url = params.get('repo_url')
        repo_name = params.get('name')
        
        if not repo_url:
            return {"error": "repo_url required for clone operation"}
        
        return _git_clone_to_clone_dir(repo_url, repo_name)
    
    # Legacy ops info
    if op == "add":
        return {"info": "Use 'add_file' (GitHub API) or 'add_paths' (local)"}
    if op == "commit":
        return {"info": "Use 'commit_all' for local, or note that GitHub 'add_file' commits automatically"}
    if op == "pull":
        return {"info": "Use local git: not implemented explicitly; script fetch+merge or use 'merge'"}
    if op == "branch":
        return {"info": "Use 'create_branch' (GitHub API) or 'branch_create' (local)"}
    
    return {"error": f"Unknown operation: {operation}"}


def _github_api_request(method: str, endpoint: str, data=None, params=None) -> Dict[str, Any]:
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        return {"error": "GITHUB_TOKEN environment variable required"}
    headers = _get_github_headers()
    url = f"https://api.github.com{endpoint}"
    try:
        method_up = method.upper()
        if method_up == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method_up == "POST":
            response = requests.post(url, headers=headers, json=data, params=params)
        elif method_up == "PUT":
            response = requests.put(url, headers=headers, json=data, params=params)
        elif method_up == "DELETE":
            response = requests.delete(url, headers=headers, json=data, params=params)
        else:
            return {"error": f"Unsupported method: {method}"}
        if response.status_code >= 400:
            return {"error": f"GitHub API error {response.status_code}: {response.text}"}
        return response.json() if response.content else {"success": True}
    except Exception as e:
        return {"error": str(e)}


def _get_github_headers() -> dict:
    return {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "MCP-Git-Tool/3.0",
    }


def _create_or_update_file(owner: str, repo: str, path: str, content: str, message: str, branch: str = "main") -> Dict[str, Any]:
    get_resp = _github_api_request("GET", f"/repos/{owner}/{repo}/contents/{path}", params={"ref": branch})
    data = {
        "message": message,
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
        "branch": branch,
    }
    if isinstance(get_resp, dict) and "sha" in get_resp:
        data["sha"] = get_resp["sha"]
    return _github_api_request("PUT", f"/repos/{owner}/{repo}/contents/{path}", data)


def _delete_file_from_repo(owner: str, repo: str, path: str, message: str, branch: str = "main") -> Dict[str, Any]:
    get_resp = _github_api_request("GET", f"/repos/{owner}/{repo}/contents/{path}", params={"ref": branch})
    if "error" in get_resp:
        return get_resp
    if "sha" not in get_resp:
        return {"error": f"Could not get SHA for file {path}"}
    data = {"message": message, "sha": get_resp["sha"], "branch": branch}
    return _github_api_request("DELETE", f"/repos/{owner}/{repo}/contents/{path}", data)


def _git_clone_to_clone_dir(repo_url: str, repo_name: Optional[str] = None) -> Dict[str, Any]:
    try:
        project_root = find_project_root()
        clone_dir = project_root / "clone"
        clone_dir.mkdir(exist_ok=True)
        if not repo_name:
            if repo_url.endswith('.git'):
                repo_name = Path(repo_url).stem
            else:
                repo_name = repo_url.split('/')[-1]
        target_path = clone_dir / repo_name
        if target_path.exists():
            shutil.rmtree(target_path)
        result = subprocess.run(['git', 'clone', repo_url, str(target_path)], 
                              capture_output=True, text=True, cwd=str(project_root))
        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Repository cloned successfully to {str(target_path)}",
                "path": str(target_path),
            }
        else:
            return {"error": f"Git clone failed: {result.stderr}", "stdout": result.stdout}
    except Exception as e:
        return {"error": f"Clone operation failed: {str(e)}"}


def spec() -> Dict[str, Any]:
    base = {
        "type": "function",
        "function": {
            "name": "git",
            "displayName": "Git",
            "description": "Git unifié: opérations Git locales (CLI) et GitHub (API). Toutes les opérations locales sont limitées à la racine du projet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string"}
                },
                "required": ["operation"],
                "additionalProperties": True
            }
        }
    }
    override = _load_spec_override("git")
    if override and isinstance(override, dict):
        fn = base.get("function", {})
        ofn = override.get("function", {})
        if ofn.get("displayName"):
            fn["displayName"] = ofn["displayName"]
        if ofn.get("description"):
            fn["description"] = ofn["description"]
        if ofn.get("parameters"):
            fn["parameters"] = ofn["parameters"]
    return base
