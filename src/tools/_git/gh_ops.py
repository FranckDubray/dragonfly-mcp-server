"""GitHub-related operations for the git tool.
This module groups lightweight wrappers around the GitHub REST API
and file-content endpoints.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import base64

from .github_api import request as gh_request
from .chroot import read_file_in_chroot


# -------- Metadata / Repo ops --------

def create_repo(name: str, description: str = "", private: bool = False) -> Dict[str, Any]:
    return gh_request("POST", "/user/repos", {"name": name, "description": description, "private": private})


def get_user(username: str) -> Dict[str, Any]:
    return gh_request("GET", f"/users/{username}")


def list_repos(username: Optional[str] = None) -> Dict[str, Any]:
    if username:
        return gh_request("GET", f"/users/{username}/repos")
    return gh_request("GET", "/user/repos")


# -------- File content ops --------

def _create_or_update_file(owner: str, repo: str, path: str, content: str, message: str, branch: str = "main") -> Dict[str, Any]:
    get_resp = gh_request("GET", f"/repos/{owner}/{repo}/contents/{path}", params={"ref": branch})
    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if isinstance(get_resp, dict) and "sha" in get_resp:
        data["sha"] = get_resp["sha"]
    return gh_request("PUT", f"/repos/{owner}/{repo}/contents/{path}", data)


def add_file(owner: str, repo: str, file_path: str, repo_path: str, message: str = "", branch: str = "main") -> Dict[str, Any]:
    if not message:
        message = f"Add {repo_path}"
    content = read_file_in_chroot(file_path)
    return _create_or_update_file(owner, repo, repo_path, content, message, branch)


def add_multiple_files(owner: str, repo: str, files: List[Dict[str, str]], message: str = "Add multiple files", branch: str = "main") -> Dict[str, Any]:
    results = []
    for info in files:
        local_path = info.get("local_path"); repo_path = info.get("repo_path")
        if not local_path or not repo_path:
            results.append({"error": f"Missing local_path or repo_path in {info}"})
            continue
        try:
            content = read_file_in_chroot(local_path)
        except Exception as e:
            results.append({"error": str(e), "file": local_path})
            continue
        res = _create_or_update_file(owner, repo, repo_path, content, f"{message} - {repo_path}", branch)
        results.append({"file": repo_path, "result": res})
    return {"results": results, "total": len(files), "processed": len(results)}


def delete_file(owner: str, repo: str, path: str, message: str = "", branch: str = "main") -> Dict[str, Any]:
    if not message:
        message = f"Delete {path}"
    get_resp = gh_request("GET", f"/repos/{owner}/{repo}/contents/{path}", params={"ref": branch})
    if "error" in get_resp:
        return get_resp
    if "sha" not in get_resp:
        return {"error": f"Could not get SHA for file {path}"}
    data = {"message": message, "sha": get_resp["sha"], "branch": branch}
    return gh_request("DELETE", f"/repos/{owner}/{repo}/contents/{path}", data)


def delete_multiple_files(owner: str, repo: str, files: List[Dict[str, str] | str], message: str = "Delete multiple files", branch: str = "main") -> Dict[str, Any]:
    results = []
    for entry in files:
        if isinstance(entry, str):
            path = entry
        elif isinstance(entry, dict) and "repo_path" in entry:
            path = entry["repo_path"]
        else:
            results.append({"error": f"Invalid file entry: {entry}"})
            continue
        res = delete_file(owner, repo, path, f"{message} - {path}", branch)
        results.append({"file": path, "result": res})
    return {"results": results, "total": len(files), "processed": len(results)}


def get_repo_contents(owner: str, repo: str, path: str = "", branch: Optional[str] = None) -> Dict[str, Any]:
    endpoint = f"/repos/{owner}/{repo}/contents" + (f"/{path}" if path else "")
    params = {"ref": branch} if branch else None
    return gh_request("GET", endpoint, params=params)


def create_branch(owner: str, repo: str, branch_name: str, from_branch: str = "main") -> Dict[str, Any]:
    ref_response = gh_request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{from_branch}")
    if "object" not in ref_response:
        return {"error": f"Could not get SHA for branch {from_branch}", "details": ref_response}
    sha = ref_response["object"]["sha"]
    data = {"ref": f"refs/heads/{branch_name}", "sha": sha}
    return gh_request("POST", f"/repos/{owner}/{repo}/git/refs", data)


def get_commits(owner: str, repo: str, branch: str = "main", count: int = 5) -> Dict[str, Any]:
    import requests
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/commits",
        params={"sha": branch, "per_page": count},
        headers=_get_github_headers(),
    )
    if r.status_code >= 400:
        return {"error": f"GitHub API error {r.status_code}: {r.text}"}
    commits = r.json()
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


def diff(owner: str, repo: str, base: str, head: str) -> Dict[str, Any]:
    return gh_request("GET", f"/repos/{owner}/{repo}/compare/{base}...{head}")


def merge(owner: str, repo: str, base: str, head: str, commit_title: Optional[str] = None, commit_message: Optional[str] = None) -> Dict[str, Any]:
    data = {"base": base, "head": head}
    if commit_title:
        data["commit_title"] = commit_title
    if commit_message:
        data["commit_message"] = commit_message
    return gh_request("POST", f"/repos/{owner}/{repo}/merges", data)


# local import to fetch headers for get_commits
from .github_api import get_headers as _get_github_headers
