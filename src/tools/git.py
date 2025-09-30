
"""
Git Tool - ultra thin facade. Heavy logic in src/tools/_git/*
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json

from ._git.local_ops import GitLocalOps
from ._git.chroot import sanitize_repo_dir, sanitize_paths_within_repo
from ._git.gh_ops import (
    create_repo as gh_create_repo,
    get_user as gh_get_user,
    list_repos as gh_list_repos,
    add_file as gh_add_file,
    add_multiple_files as gh_add_multiple_files,
    delete_file as gh_delete_file,
    delete_multiple_files as gh_delete_multiple_files,
    get_repo_contents as gh_get_repo_contents,
    create_branch as gh_create_branch,
    get_commits as gh_get_commits,
    diff as gh_diff,
    merge as gh_merge,
)
from ._git.high_level import (
    op_ensure_repo,
    op_config_user,
    op_set_remote,
    op_sync_repo,
)

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


def run(operation: str, **params) -> Union[Dict[str, Any], str]:
    op = (operation or "").strip()

    # GitHub API ops
    if op == "create_repo":
        if not params.get("name"):
            return {"error": "repository name required"}
        return gh_create_repo(params.get("name"), params.get("description", ""), params.get("private", False))

    if op == "get_user":
        if not params.get("username"):
            return {"error": "username required"}
        return gh_get_user(params.get("username"))

    if op == "list_repos":
        return gh_list_repos(params.get("username"))

    if op == "add_file":
        required = [params.get("owner"), params.get("repo"), params.get("file_path"), params.get("repo_path")]
        if not all(required):
            return {"error": "owner, repo, file_path, and repo_path required"}
        return gh_add_file(params.get("owner"), params.get("repo"), params.get("file_path"), params.get("repo_path"), params.get("message", ""), params.get("branch", "main"))

    if op == "add_multiple_files":
        required = [params.get("owner"), params.get("repo"), params.get("files")]
        if not all(required):
            return {"error": "owner, repo, and files list required"}
        return gh_add_multiple_files(params.get("owner"), params.get("repo"), params.get("files", []), params.get("message", "Add multiple files"), params.get("branch", "main"))

    if op == "delete_file":
        required = [params.get("owner"), params.get("repo"), params.get("file_path")]
        if not all(required):
            return {"error": "owner, repo, and file_path required"}
        return gh_delete_file(params.get("owner"), params.get("repo"), params.get("file_path"), params.get("message", ""), params.get("branch", "main"))

    if op == "delete_multiple_files":
        required = [params.get("owner"), params.get("repo"), params.get("files")]
        if not all(required):
            return {"error": "owner, repo, and files list required"}
        return gh_delete_multiple_files(params.get("owner"), params.get("repo"), params.get("files", []), params.get("message", "Delete multiple files"), params.get("branch", "main"))

    if op == "get_repo_contents":
        required = [params.get("owner"), params.get("repo")]
        if not all(required):
            return {"error": "owner and repo required"}
        return gh_get_repo_contents(params.get("owner"), params.get("repo"), params.get("path", ""), params.get("branch"))

    if op == "create_branch":
        required = [params.get("owner"), params.get("repo"), params.get("branch_name")]
        if not all(required):
            return {"error": "owner, repo, and branch_name required"}
        return gh_create_branch(params.get("owner"), params.get("repo"), params.get("branch_name"), params.get("from_branch", "main"))

    if op == "get_commits":
        required = [params.get("owner"), params.get("repo")]
        if not all(required):
            return {"error": "owner and repo required"}
        return gh_get_commits(params.get("owner"), params.get("repo"), params.get("branch", "main"), params.get("count", 5))

    if op == "diff":
        required = [params.get("owner"), params.get("repo"), params.get("head")]
        if not all(required):
            return {"error": "owner, repo, and head required for diff"}
        return gh_diff(params.get("owner"), params.get("repo"), params.get("base", "main"), params.get("head"))

    if op == "merge":
        owner = params.get("owner"); repo = params.get("repo")
        if owner and repo:
            base = params.get("base"); head = params.get("head")
            if not all([base, head]):
                return {"error": "base and head required for GitHub merge"}
            return gh_merge(owner, repo, base, head, params.get("commit_title"), params.get("message") or params.get("commit_message"))
        # else local merge passthrough
        local_ops = GitLocalOps()
        repo_dir = sanitize_repo_dir(params.get('repo_dir'))
        source = params.get('source') or params.get('head') or params.get('from_branch')
        if not source:
            return {"error": "source (branch to merge) required for local merge"}
        return local_ops.handle_merge(repo_dir, source, **params)

    # Local git passthrough
    if op in ["status", "branch_create", "checkout", "add_paths", "commit_all", "push"]:
        local_ops = GitLocalOps()
        repo_dir = sanitize_repo_dir(params.get('repo_dir'))
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
            paths = sanitize_paths_within_repo(repo_dir, paths)
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

    # High-level orchestrated ops
    if op == "ensure_repo":
        return op_ensure_repo(params.get('repo_dir'), params.get('branch', 'main'))
    if op == "config_user":
        return op_config_user(params.get('repo_dir'), params.get('name'), params.get('email'))
    if op == "set_remote":
        return op_set_remote(params.get('repo_dir'), params.get('owner'), params.get('repo'), params.get('overwrite', True))
    if op == "sync_repo":
        return op_sync_repo(**params)

    return {"error": f"Unknown operation: {operation}"}


def spec() -> Dict[str, Any]:
    base = {
        "type": "function",
        "function": {
            "name": "git",
            "displayName": "Git",
            "description": "Git unifié: GitHub API + Git local. High-level: ensure_repo, config_user, set_remote, sync_repo (push tout le dépôt).",
            "parameters": {
                "type": "object",
                "properties": {"operation": {"type": "string"}},
                "required": ["operation"],
                "additionalProperties": True
            }
        }
    }
    override = _load_spec_override("git")
    if override and isinstance(override, dict):
        fn = base.get("function", {})
        ofn = override.get("function", {})
        if ofn.get("displayName"): fn["displayName"] = ofn["displayName"]
        if ofn.get("description"): fn["description"] = ofn["description"]
        if ofn.get("parameters"): fn["parameters"] = ofn["parameters"]
    return base
