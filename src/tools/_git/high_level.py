"""High-level operations exposed by the Git tool: ensure_repo, config_user, set_remote, sync_repo.
Thin orchestration layer that composes lower-level helpers.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .chroot import resolve_in_chroot, sanitize_repo_dir
from .local_ops import GitLocalOps
from .sync_ops import ensure_repo as _ensure_repo, config_user as _config_user, set_remote as _set_remote, sync_repo as _sync_repo


def op_ensure_repo(repo_dir: Optional[str], branch: str = "main") -> Dict[str, Any]:
    return _ensure_repo(repo_dir=repo_dir, branch=branch)


def op_config_user(repo_dir: Optional[str], name: Optional[str], email: Optional[str]) -> Dict[str, Any]:
    return _config_user(repo_dir=repo_dir, name=name, email=email)


def op_set_remote(repo_dir: Optional[str], owner: str, repo: str, overwrite: bool = True) -> Dict[str, Any]:
    return _set_remote(repo_dir=repo_dir, owner=owner, repo=repo, overwrite=overwrite)


def op_sync_repo(**params: Any) -> Dict[str, Any]:
    return _sync_repo(
        owner=params.get('owner'),
        repo=params.get('repo'),
        branch=params.get('branch', 'main'),
        message=params.get('message') or params.get('commit_message') or 'Sync from MCP',
        repo_dir=params.get('repo_dir'),
        visibility=params.get('visibility', 'private'),
        overwrite_remote=params.get('overwrite_remote', True),
        user_name=params.get('user_name'),
        user_email=params.get('user_email'),
    )
