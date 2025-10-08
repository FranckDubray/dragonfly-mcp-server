"""Local Git operations via CLI."""
import subprocess
from pathlib import Path
from typing import Any, Dict, List

class GitLocalOps:
    def _run(self, cmd: List[str], cwd: Path) -> Dict[str, Any]:
        try:
            res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
            return {
                "returncode": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "ok": res.returncode == 0,
                "cmd": cmd,
                "cwd": str(cwd),
            }
        except FileNotFoundError:
            return {"ok": False, "error": "git not found in PATH", "cmd": cmd, "cwd": str(cwd)}
        except Exception as e:
            return {"ok": False, "error": str(e), "cmd": cmd, "cwd": str(cwd)}

    def handle_status(self, repo_dir: Path) -> Dict[str, Any]:
        head = self._run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_dir)
        por = self._run(["git", "status", "--porcelain"], repo_dir)
        rem = self._run(["git", "remote", "-v"], repo_dir)
        return {
            "success": head.get("ok", False) and por.get("ok", False),
            "repo_path": str(repo_dir),
            "branch": head.get("stdout", "").strip(),
            "changes": por.get("stdout", ""),
            "remotes": rem.get("stdout", ""),
            "errors": [e for e in [head.get("stderr"), por.get("stderr"), rem.get("stderr")] if e],
        }

    def handle_fetch(self, repo_dir: Path, remote: str = "origin", prune: bool = False) -> Dict[str, Any]:
        """Fetch updates from remote without merging"""
        cmd = ["git", "fetch", remote]
        if prune:
            cmd.append("--prune")
        res = self._run(cmd, repo_dir)
        return {"success": res["ok"], "result": res}

    def handle_pull(self, repo_dir: Path, remote: str = "origin", branch: str = None, 
                   rebase: bool = False, ff_only: bool = False) -> Dict[str, Any]:
        """Pull changes from remote (fetch + merge or rebase)"""
        cmd = ["git", "pull"]
        
        if rebase:
            cmd.append("--rebase")
        if ff_only:
            cmd.append("--ff-only")
        
        cmd.append(remote)
        if branch:
            cmd.append(branch)
        
        res = self._run(cmd, repo_dir)
        result = {"success": res.get("ok", False), "result": res}
        
        # Check for conflicts
        if not res.get("ok", False):
            conflicts = self._get_conflicts(repo_dir)
            if conflicts:
                result["conflicts"] = conflicts
                result["hint"] = "Resolve conflicts then run: git rebase --continue (if rebase) or git merge --continue (if merge)"
        
        return result

    def handle_rebase(self, repo_dir: Path, branch: str = None, 
                     continue_rebase: bool = False, abort: bool = False, skip: bool = False) -> Dict[str, Any]:
        """Rebase current branch onto another branch"""
        cmd = ["git", "rebase"]
        
        if continue_rebase:
            cmd.append("--continue")
        elif abort:
            cmd.append("--abort")
        elif skip:
            cmd.append("--skip")
        elif branch:
            cmd.append(branch)
        else:
            return {"error": "branch parameter required (or use continue_rebase/abort/skip)"}
        
        res = self._run(cmd, repo_dir)
        result = {"success": res.get("ok", False), "result": res}
        
        # Check for conflicts
        if not res.get("ok", False) and not abort:
            conflicts = self._get_conflicts(repo_dir)
            if conflicts:
                result["conflicts"] = conflicts
                result["hint"] = "Resolve conflicts then run rebase with continue_rebase=true"
        
        return result

    def handle_branch_create(self, repo_dir: Path, branch_name: str, from_branch: str = None) -> Dict[str, Any]:
        if from_branch:
            chk = self._run(["git", "checkout", from_branch], repo_dir)
            if not chk["ok"]:
                return {"error": f"checkout {from_branch} failed", "details": chk}
        res = self._run(["git", "checkout", "-b", branch_name], repo_dir)
        return {"success": res["ok"], "result": res}

    def handle_checkout(self, repo_dir: Path, branch: str) -> Dict[str, Any]:
        res = self._run(["git", "checkout", branch], repo_dir)
        return {"success": res["ok"], "result": res}

    def handle_add_paths(self, repo_dir: Path, paths: List[str]) -> Dict[str, Any]:
        res = self._run(["git", "add", "-A", *paths], repo_dir)
        return {"success": res["ok"], "result": res}

    def handle_commit_all(self, repo_dir: Path, message: str) -> Dict[str, Any]:
        add_res = self._run(["git", "add", "-A"], repo_dir)
        if not add_res["ok"]:
            return {"error": "git add failed", "result": add_res}
        res = self._run(["git", "commit", "-m", message], repo_dir)
        return {"success": res["ok"], "result": res}

    def handle_push(self, repo_dir: Path, branch: str, remote: str = "origin", 
                   set_upstream: bool = True, force: bool = False) -> Dict[str, Any]:
        cmd = ["git", "push"]
        if force:
            cmd.append("--force-with-lease")
        if set_upstream:
            cmd += ["-u", remote, branch]
        else:
            cmd += [remote, branch]
        res = self._run(cmd, repo_dir)
        return {"success": res["ok"], "result": res}

    def handle_merge(self, repo_dir: Path, source: str, **options) -> Dict[str, Any]:
        cmd = ["git", "merge"]
        if options.get('no_ff'):
            cmd.append("--no-ff")
        if options.get('squash'):
            cmd.append("--squash")
        if options.get('ff_only'):
            cmd.append("--ff-only")
        if options.get('no_commit'):
            cmd.append("--no-commit")
        if options.get('message'):
            cmd.extend(["-m", options['message']])
        cmd.append(source)
        
        res = self._run(cmd, repo_dir)
        result = {"success": res.get("ok", False), "result": res}
        
        # If merge failed, check for conflicts
        if not res.get("ok", False):
            conflicts = self._get_conflicts(repo_dir)
            result["conflicts"] = conflicts
        
        return result

    def handle_log(self, repo_dir: Path, max_count: int = 10, 
                  one_line: bool = False, graph: bool = False) -> Dict[str, Any]:
        """Get commit history"""
        cmd = ["git", "log", f"--max-count={max_count}"]
        if one_line:
            cmd.append("--oneline")
        if graph:
            cmd.append("--graph")
        
        res = self._run(cmd, repo_dir)
        return {"success": res["ok"], "result": res}

    def handle_remote_info(self, repo_dir: Path) -> Dict[str, Any]:
        """Get remote repository information"""
        remotes = self._run(["git", "remote", "-v"], repo_dir)
        url = self._run(["git", "config", "--get", "remote.origin.url"], repo_dir)
        
        return {
            "success": remotes["ok"],
            "remotes": remotes.get("stdout", ""),
            "origin_url": url.get("stdout", "").strip()
        }

    def _get_conflicts(self, repo_dir: Path) -> List[str]:
        st = self._run(["git", "status", "--porcelain"], repo_dir)
        if not st.get("ok"):
            return []
        conflicts = []
        for line in st.get("stdout", "").splitlines():
            if len(line) < 3:
                continue
            code = line[0:2]
            path = line[3:]
            if code in {"AA", "UU", "DD", "AU", "UA", "DU", "UD"} or code.startswith("U"):
                conflicts.append(path)
        return conflicts
