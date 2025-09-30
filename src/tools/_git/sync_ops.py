"""High-level sync operations for the Git tool.
Keep heavy logic here (not in src/tools/git.py) to ease maintenance.
"""
from __future__ import annotations
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

try:
    from config import find_project_root
except ImportError:  # Fallback for tests
    find_project_root = lambda: Path.cwd()

# -----------------------------
# Chroot helpers
# -----------------------------

def _chroot_base() -> Path:
    return find_project_root().resolve()


def _resolve_repo_dir(rel_path: Optional[str]) -> Path:
    base = _chroot_base()
    if not rel_path or str(rel_path).strip() in ("", ".", "/"):
        return base
    p = (base / rel_path).resolve()
    if not str(p).startswith(str(base)):
        raise ValueError("repo_dir escapes project root")
    return p

# -----------------------------
# Process helpers
# -----------------------------

def _mask_secret(text: str, secret: Optional[str]) -> str:
    if not (isinstance(text, str) and secret):
        return text
    try:
        return text.replace(secret, "***")
    except Exception:
        return text


def _run_git(args: List[str], cwd: Path, secret: Optional[str] = None) -> Dict[str, Any]:
    try:
        res = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
        return {
            "ok": res.returncode == 0,
            "returncode": res.returncode,
            "cmd": "git " + " ".join(_mask_secret(a, secret) for a in args),
            "cwd": str(cwd),
            "stdout": _mask_secret(res.stdout, secret),
            "stderr": _mask_secret(res.stderr, secret),
        }
    except FileNotFoundError:
        return {"ok": False, "error": "git not found in PATH", "cmd": f"git {' '.join(args)}", "cwd": str(cwd)}
    except Exception as e:
        return {"ok": False, "error": str(e), "cmd": f"git {' '.join(args)}", "cwd": str(cwd)}

# -----------------------------
# GitHub helpers
# -----------------------------

def _github_headers() -> Dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    return {
        "Authorization": f"token {token}" if token else "",
        "Accept": "application/vnd.github+json",
        "User-Agent": "MCP-Git-Tool/3.0",
    }


def _github_api_request(method: str, endpoint: str, data=None, params=None) -> Dict[str, Any]:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return {"error": "GITHUB_TOKEN environment variable required"}
    url = f"https://api.github.com{endpoint}"
    try:
        m = method.upper()
        if m == "GET":
            r = requests.get(url, headers=_github_headers(), params=params)
        elif m == "POST":
            r = requests.post(url, headers=_github_headers(), json=data, params=params)
        elif m == "PUT":
            r = requests.put(url, headers=_github_headers(), json=data, params=params)
        elif m == "DELETE":
            r = requests.delete(url, headers=_github_headers(), json=data, params=params)
        else:
            return {"error": f"Unsupported method: {method}"}
        if r.status_code >= 400:
            return {"error": f"GitHub API error {r.status_code}: {r.text}"}
        return r.json() if r.content else {"success": True}
    except Exception as e:
        return {"error": str(e)}


def _ensure_github_repo(owner: str, name: str, private: bool) -> Dict[str, Any]:
    exists = _github_api_request("GET", f"/repos/{owner}/{name}")
    if isinstance(exists, dict) and exists.get("id"):
        return {"exists": True, "repo": exists}
    created = _github_api_request("POST", "/user/repos", {
        "name": name,
        "private": private,
        "description": "Published by Dragonfly MCP Server",
    })
    return {"exists": False, "repo": created}

# -----------------------------
# High-level ops
# -----------------------------

def ensure_repo(repo_dir: Optional[str] = None, branch: str = "main") -> Dict[str, Any]:
    repo_path = _resolve_repo_dir(repo_dir)
    steps: List[Dict[str, Any]] = []
    # init if needed
    if not (repo_path / ".git").is_dir():
        steps.append(_run_git(["init", "-b", branch], repo_path))
    # ensure branch
    cur = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
    steps.append(cur)
    if (cur.get("ok") and cur.get("stdout", "").strip() != branch) or (not cur.get("ok")):
        steps.append(_run_git(["checkout", "-B", branch], repo_path))
    ok = all(s.get("ok", True) for s in steps if isinstance(s, dict))
    return {"success": ok, "repo_dir": str(repo_path), "branch": branch, "steps": steps}


def config_user(repo_dir: Optional[str] = None, name: Optional[str] = None, email: Optional[str] = None) -> Dict[str, Any]:
    repo_path = _resolve_repo_dir(repo_dir)
    steps: List[Dict[str, Any]] = []
    if name:
        steps.append(_run_git(["config", "user.name", name], repo_path))
    if email:
        steps.append(_run_git(["config", "user.email", email], repo_path))
    ok = all(s.get("ok", True) for s in steps if isinstance(s, dict)) if steps else True
    return {"success": ok, "repo_dir": str(repo_path), "result": steps}


def set_remote(repo_dir: Optional[str] = None, owner: Optional[str] = None, repo: Optional[str] = None, overwrite: bool = True) -> Dict[str, Any]:
    token = os.getenv("GITHUB_TOKEN")
    if not (owner and repo and token):
        return {"error": "owner, repo and GITHUB_TOKEN required"}
    repo_path = _resolve_repo_dir(repo_dir)
    url = f"https://{token}:x-oauth-basic@github.com/{owner}/{repo}.git"
    steps: List[Dict[str, Any]] = []
    if overwrite:
        steps.append(_run_git(["remote", "remove", "origin"], repo_path, secret=token))
    setres = _run_git(["remote", "set-url", "origin", url], repo_path, secret=token)
    if not setres.get("ok"):
        steps.append(setres)
        steps.append(_run_git(["remote", "add", "origin", url], repo_path, secret=token))
    else:
        steps.append(setres)
    ok = all(s.get("ok", True) for s in steps if isinstance(s, dict))
    return {"success": ok, "repo_dir": str(repo_path), "steps": steps}


def sync_repo(
    owner: str,
    repo: str,
    branch: str = "main",
    message: str = "Sync from MCP",
    repo_dir: Optional[str] = None,
    visibility: str = "private",
    overwrite_remote: bool = True,
    user_name: Optional[str] = None,
    user_email: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return {"error": "GITHUB_TOKEN environment variable required"}

    repo_path = _resolve_repo_dir(repo_dir)
    private = (visibility != "public")

    steps: List[Dict[str, Any]] = []

    # 1) Ensure repo + branch
    res_ensure = ensure_repo(repo_dir=repo_dir, branch=branch)
    steps.append({"op": "ensure_repo", **res_ensure})

    # 2) Optional user config
    if user_name or user_email:
        res_cfg = config_user(repo_dir=repo_dir, name=user_name, email=user_email)
        steps.append({"op": "config_user", **res_cfg})

    # 3) Stage + commit only if changes
    steps.append(_run_git(["add", "-A"], repo_path))
    stat = _run_git(["status", "--porcelain"], repo_path)
    steps.append(stat)
    if stat.get("stdout", "").strip():
        steps.append(_run_git(["commit", "-m", message], repo_path))

    # 4) Ensure GitHub repo exists
    gh = _ensure_github_repo(owner, repo, private)

    # 5) Ensure remote with token, then push
    res_remote = set_remote(repo_dir=repo_dir, owner=owner, repo=repo, overwrite=overwrite_remote)
    steps.append({"op": "set_remote", **res_remote})

    steps.append(_run_git(["push", "-u", "origin", branch], repo_path, secret=token))

    success = all(
        (s.get("success", s.get("ok", True))) if isinstance(s, dict) else True
        for s in steps
    )
    return {
        "success": success,
        "repo_dir": str(repo_path),
        "branch": branch,
        "created_github_repo": not gh.get("exists", True),
        "github": gh,
        "steps": steps,
    }
