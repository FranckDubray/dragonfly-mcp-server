"""GitHub API helpers for the Git tool."""
from __future__ import annotations
import os
from typing import Dict, Any, Optional
import requests


def get_headers() -> Dict[str, str]:
    token = os.getenv("GITHUB_TOKEN")
    return {
        "Authorization": f"token {token}" if token else "",
        "Accept": "application/vnd.github+json",
        "User-Agent": "MCP-Git-Tool/3.0",
    }


def request(method: str, endpoint: str, data: Optional[dict] = None, params: Optional[dict] = None) -> Dict[str, Any]:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return {"error": "GITHUB_TOKEN environment variable required"}
    url = f"https://api.github.com{endpoint}"
    m = method.upper()
    try:
        if m == "GET":
            r = requests.get(url, headers=get_headers(), params=params)
        elif m == "POST":
            r = requests.post(url, headers=get_headers(), json=data, params=params)
        elif m == "PUT":
            r = requests.put(url, headers=get_headers(), json=data, params=params)
        elif m == "DELETE":
            r = requests.delete(url, headers=get_headers(), json=data, params=params)
        else:
            return {"error": f"Unsupported method: {method}"}
        if r.status_code >= 400:
            return {"error": f"GitHub API error {r.status_code}: {r.text}"}
        return r.json() if r.content else {"success": True}
    except Exception as e:
        return {"error": str(e)}


def ensure_repo(owner: str, name: str, private: bool) -> Dict[str, Any]:
    exists = request("GET", f"/repos/{owner}/{name}")
    if isinstance(exists, dict) and exists.get("id"):
        return {"exists": True, "repo": exists}
    created = request("POST", "/user/repos", {"name": name, "private": private, "description": "Published by Dragonfly MCP Server"})
    return {"exists": False, "repo": created}
