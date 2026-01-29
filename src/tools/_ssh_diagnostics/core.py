"""SSH Diagnostics - Core logic"""
from typing import Dict, Any
import subprocess
import logging
import platform
import shutil

logger = logging.getLogger(__name__)


def _run_command(cmd: list, timeout: int = 30, capture_stderr: bool = True) -> Dict[str, Any]:
    """Run shell command safely.
    
    Args:
        cmd: Command as list (e.g., ['ssh', '-vvv', 'host'])
        timeout: Timeout in seconds
        capture_stderr: Capture stderr in output
        
    Returns:
        Dict with stdout, stderr, returncode, error
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        
        output = {
            "stdout": result.stdout,
            "returncode": result.returncode,
            "command": " ".join(cmd)
        }
        
        if capture_stderr:
            output["stderr"] = result.stderr
        
        return output
        
    except subprocess.TimeoutExpired:
        return {"error": f"Command timeout after {timeout}s", "command": " ".join(cmd)}
    except Exception as e:
        return {"error": f"Command failed: {str(e)}", "command": " ".join(cmd)}


def test_connection(host: str, user: str = "root", port: int = 22, 
                   ssh_key_path: str = None, timeout: int = 30, **kwargs) -> Dict[str, Any]:
    """Test SSH connection with verbose output (simulated, safe).
    
    ⚠️ NOTE: This does NOT actually connect (to avoid auth prompts).
    Instead, it simulates what 'ssh -vvv' would show and provides guidance.
    
    Args:
        host: SSH server hostname/IP
        user: SSH username
        port: SSH port
        ssh_key_path: Path to SSH key (optional)
        timeout: Command timeout
        
    Returns:
        Diagnostic guidance and command to run manually
    """
    cmd_parts = ["ssh", "-vvv"]
    
    if ssh_key_path:
        cmd_parts.extend(["-i", ssh_key_path])
    
    if port != 22:
        cmd_parts.extend(["-p", str(port)])
    
    cmd_parts.append(f"{user}@{host}")
    cmd_str = " ".join(cmd_parts)
    
    return {
        "operation": "test_connection",
        "status": "instruction",
        "message": "Pour diagnostiquer la déconnexion, exécutez cette commande MANUELLEMENT dans votre terminal local",
        "command": cmd_str,
        "instructions": [
            "1. Ouvrez un terminal sur votre PC (PowerShell/Terminal/iTerm)",
            "2. Exécutez la commande ci-dessus",
            "3. Laissez tourner jusqu'à la déconnexion",
            "4. Notez les dernières lignes affichées (debug3, packet_write_wait, etc.)",
            "5. Recherchez : 'Connection reset', 'Broken pipe', 'timeout', 'kex_exchange'"
        ],
        "what_to_look_for": [
            "Connection reset by peer → firewall/serveur coupe",
            "Broken pipe → timeout NAT/routeur",
            "packet_write_wait: Connection to ... broken → timeout idle",
            "kex_exchange_identification → problème réseau initial"
        ]
    }


def check_server_logs(log_lines: int = 100, timeout: int = 30, **kwargs) -> Dict[str, Any]:
    """Check SSH server logs (Debian/Ubuntu: auth.log, RHEL: secure).
    
    Args:
        log_lines: Number of log lines to retrieve
        timeout: Command timeout
        
    Returns:
        Server SSH logs
    """
    # Detect OS
    is_linux = platform.system() == "Linux"
    
    if not is_linux:
        return {
            "operation": "check_server_logs",
            "status": "local_only",
            "message": "Cette opération doit être exécutée SUR le serveur SSH distant",
            "manual_commands": [
                "# Sur Debian/Ubuntu:",
                f"sudo journalctl -u ssh -n {log_lines} --no-pager",
                f"# OU",
                f"sudo tail -n {log_lines} /var/log/auth.log",
                "",
                "# Sur CentOS/Rocky/Alma:",
                f"sudo tail -n {log_lines} /var/log/secure"
            ]
        }
    
    # Try journalctl first (systemd)
    if shutil.which("journalctl"):
        result = _run_command(["journalctl", "-u", "ssh", "-n", str(log_lines), "--no-pager"], timeout)
        if result.get("returncode") == 0:
            return {
                "operation": "check_server_logs",
                "source": "journalctl",
                "lines_requested": log_lines,
                "logs": result["stdout"],
                "hint": "Cherchez : 'Disconnected', 'timeout', 'Connection reset', 'preauth', IP bannie"
            }
    
    # Fallback to log files
    log_paths = ["/var/log/auth.log", "/var/log/secure"]
    for log_path in log_paths:
        result = _run_command(["tail", "-n", str(log_lines), log_path], timeout)
        if result.get("returncode") == 0:
            return {
                "operation": "check_server_logs",
                "source": log_path,
                "lines_requested": log_lines,
                "logs": result["stdout"],
                "hint": "Cherchez : 'Disconnected', 'timeout', 'Connection reset', 'preauth', IP bannie"
            }
    
    return {
        "operation": "check_server_logs",
        "status": "error",
        "error": "Impossible de lire les logs (ni journalctl, ni /var/log/{auth.log,secure})"
    }


def check_keepalive_config(timeout: int = 30, **kwargs) -> Dict[str, Any]:
    """Check SSH keepalive configuration on server.
    
    Args:
        timeout: Command timeout
        
    Returns:
        Current keepalive config
    """
    if platform.system() != "Linux":
        return {
            "operation": "check_keepalive_config",
            "status": "local_only",
            "manual_command": "grep -E '(ClientAlive|TCPKeepAlive)' /etc/ssh/sshd_config"
        }
    
    result = _run_command(
        ["grep", "-E", "(ClientAlive|TCPKeepAlive)", "/etc/ssh/sshd_config"],
        timeout
    )
    
    config = result.get("stdout", "")
    
    return {
        "operation": "check_keepalive_config",
        "current_config": config if config else "Aucune config keepalive explicite trouvée",
        "recommendation": {
            "ClientAliveInterval": 30,
            "ClientAliveCountMax": 6,
            "explanation": "Envoi keepalive toutes les 30s, déconnexion après 6 échecs (180s total)"
        },
        "how_to_apply": [
            "1. sudo nano /etc/ssh/sshd_config",
            "2. Ajouter/modifier :",
            "   ClientAliveInterval 30",
            "   ClientAliveCountMax 6",
            "3. sudo systemctl reload ssh"
        ]
    }


def test_network(host: str, mtr_count: int = 50, timeout: int = 60, **kwargs) -> Dict[str, Any]:
    """Test network connectivity (ping, traceroute, mtr).
    
    Args:
        host: Target host
        mtr_count: Number of MTR packets
        timeout: Command timeout
        
    Returns:
        Network test results
    """
    results = {"operation": "test_network", "host": host, "tests": {}}
    
    # Ping test
    ping_cmd = ["ping", "-c", "4", host]
    if platform.system() == "Windows":
        ping_cmd = ["ping", "-n", "4", host]
    
    ping_result = _run_command(ping_cmd, timeout=10)
    results["tests"]["ping"] = {
        "command": " ".join(ping_cmd),
        "output": ping_result.get("stdout", ""),
        "success": ping_result.get("returncode") == 0
    }
    
    # Traceroute (if available)
    traceroute_bin = shutil.which("traceroute") or shutil.which("tracert")
    if traceroute_bin:
        tr_cmd = [traceroute_bin, host]
        tr_result = _run_command(tr_cmd, timeout=30)
        results["tests"]["traceroute"] = {
            "command": " ".join(tr_cmd),
            "output": tr_result.get("stdout", "")[:2000],  # Truncate
            "success": tr_result.get("returncode") == 0
        }
    else:
        results["tests"]["traceroute"] = {"status": "not_available"}
    
    # MTR (if available)
    if shutil.which("mtr"):
        mtr_cmd = ["mtr", "-rwzbc", str(mtr_count), host]
        mtr_result = _run_command(mtr_cmd, timeout=timeout)
        results["tests"]["mtr"] = {
            "command": " ".join(mtr_cmd),
            "output": mtr_result.get("stdout", "")[:3000],  # Truncate
            "success": mtr_result.get("returncode") == 0,
            "hint": "Cherchez % de perte (Loss%) et latence (Avg) par hop"
        }
    else:
        results["tests"]["mtr"] = {
            "status": "not_installed",
            "install": "sudo apt install mtr-tiny  # Debian/Ubuntu\nsudo yum install mtr  # RHEL"
        }
    
    return results


def check_firewall(timeout: int = 30, **kwargs) -> Dict[str, Any]:
    """Check firewall rules (iptables, nft, ufw).
    
    Args:
        timeout: Command timeout
        
    Returns:
        Firewall status
    """
    if platform.system() != "Linux":
        return {
            "operation": "check_firewall",
            "status": "local_only",
            "manual_commands": [
                "sudo iptables -S",
                "sudo nft list ruleset",
                "sudo ufw status verbose"
            ]
        }
    
    results = {"operation": "check_firewall", "checks": {}}
    
    # UFW
    if shutil.which("ufw"):
        ufw_result = _run_command(["sudo", "ufw", "status", "verbose"], timeout)
        results["checks"]["ufw"] = {
            "output": ufw_result.get("stdout", ""),
            "available": True
        }
    
    # iptables
    if shutil.which("iptables"):
        ipt_result = _run_command(["sudo", "iptables", "-S"], timeout)
        results["checks"]["iptables"] = {
            "output": ipt_result.get("stdout", "")[:2000],  # Truncate
            "available": True,
            "hint": "Cherchez règles DROP/REJECT sur port 22"
        }
    
    # nftables
    if shutil.which("nft"):
        nft_result = _run_command(["sudo", "nft", "list", "ruleset"], timeout)
        results["checks"]["nftables"] = {
            "output": nft_result.get("stdout", "")[:2000],  # Truncate
            "available": True
        }
    
    if not results["checks"]:
        results["message"] = "Aucun firewall détecté (ufw, iptables, nft)"
    
    return results


def check_fail2ban(timeout: int = 30, **kwargs) -> Dict[str, Any]:
    """Check fail2ban status and SSH jail.
    
    Args:
        timeout: Command timeout
        
    Returns:
        Fail2ban status
    """
    if platform.system() != "Linux":
        return {
            "operation": "check_fail2ban",
            "status": "local_only",
            "manual_commands": [
                "sudo systemctl status fail2ban",
                "sudo fail2ban-client status sshd"
            ]
        }
    
    results = {"operation": "check_fail2ban"}
    
    # Check if fail2ban is running
    status_result = _run_command(["sudo", "systemctl", "status", "fail2ban", "--no-pager"], timeout)
    results["service_status"] = {
        "output": status_result.get("stdout", ""),
        "running": "active (running)" in status_result.get("stdout", "").lower()
    }
    
    # Check sshd jail
    if shutil.which("fail2ban-client"):
        jail_result = _run_command(["sudo", "fail2ban-client", "status", "sshd"], timeout)
        results["sshd_jail"] = {
            "output": jail_result.get("stdout", ""),
            "hint": "Vérifiez 'Currently banned' pour voir si votre IP est bannie"
        }
    
    return results


def check_server_load(timeout: int = 30, **kwargs) -> Dict[str, Any]:
    """Check server load, memory, and system logs.
    
    Args:
        timeout: Command timeout
        
    Returns:
        Server load metrics
    """
    if platform.system() != "Linux":
        return {
            "operation": "check_server_load",
            "status": "local_only",
            "manual_commands": [
                "uptime",
                "free -h",
                "top -bn1 | head -20",
                "dmesg -T | tail -n 100"
            ]
        }
    
    results = {"operation": "check_server_load", "metrics": {}}
    
    # Uptime
    uptime_result = _run_command(["uptime"], timeout)
    results["metrics"]["uptime"] = uptime_result.get("stdout", "").strip()
    
    # Free memory
    free_result = _run_command(["free", "-h"], timeout)
    results["metrics"]["memory"] = free_result.get("stdout", "")
    
    # Top (snapshot)
    top_result = _run_command(["sh", "-c", "top -bn1 | head -20"], timeout)
    results["metrics"]["top_snapshot"] = top_result.get("stdout", "")
    
    # Dmesg (recent kernel messages)
    dmesg_result = _run_command(["sh", "-c", "dmesg -T | tail -n 100"], timeout)
    results["metrics"]["dmesg"] = dmesg_result.get("stdout", "")[:3000]  # Truncate
    results["hint"] = "Cherchez : 'Out of memory', 'oom-killer', erreurs réseau"
    
    return results


def generate_ssh_config(host: str, user: str = "root", port: int = 22,
                       keepalive_interval: int = 30, keepalive_count_max: int = 6,
                       ssh_key_path: str = None, **kwargs) -> Dict[str, Any]:
    """Generate optimized SSH config for stable connections.
    
    Args:
        host: SSH server hostname/IP
        user: SSH username
        port: SSH port
        keepalive_interval: ServerAliveInterval in seconds
        keepalive_count_max: ServerAliveCountMax
        ssh_key_path: Path to SSH key (optional)
        
    Returns:
        SSH config snippet
    """
    config_lines = [
        f"Host hetzner",
        f"  HostName {host}",
        f"  User {user}",
        f"  Port {port}",
        f"  ServerAliveInterval {keepalive_interval}",
        f"  ServerAliveCountMax {keepalive_count_max}",
        f"  TCPKeepAlive yes"
    ]
    
    if ssh_key_path:
        config_lines.append(f"  IdentityFile {ssh_key_path}")
    
    config_text = "\n".join(config_lines)
    
    # Detect home directory
    home_dir = "~"
    if platform.system() == "Windows":
        home_dir = "%USERPROFILE%"
    
    return {
        "operation": "generate_ssh_config",
        "config": config_text,
        "instructions": [
            f"1. Éditez {home_dir}/.ssh/config (créez-le si inexistant)",
            "2. Ajoutez le bloc ci-dessus",
            "3. Sauvegardez",
            "4. Connectez-vous avec : ssh hetzner",
            "",
            "Explication :",
            f"- ServerAliveInterval {keepalive_interval} : envoie un keepalive toutes les {keepalive_interval}s",
            f"- ServerAliveCountMax {keepalive_count_max} : déconnecte après {keepalive_count_max} échecs ({keepalive_interval * keepalive_count_max}s total)",
            "- TCPKeepAlive yes : keepalive TCP en plus (doublon mais utile)"
        ],
        "platform_note": "Windows: fichier dans %USERPROFILE%\\.ssh\\config" if platform.system() == "Windows" else "Unix: fichier dans ~/.ssh/config"
    }


def full_diagnostic(host: str, user: str = "root", port: int = 22,
                   log_lines: int = 100, mtr_count: int = 50, 
                   timeout: int = 60, **kwargs) -> Dict[str, Any]:
    """Run complete SSH diagnostic suite.
    
    Args:
        host: SSH server hostname/IP
        user: SSH username
        port: SSH port
        log_lines: Log lines to retrieve
        mtr_count: MTR packet count
        timeout: Command timeout
        
    Returns:
        Comprehensive diagnostic report
    """
    logger.info(f"Running full SSH diagnostic for {user}@{host}:{port}")
    
    report = {
        "operation": "full_diagnostic",
        "target": f"{user}@{host}:{port}",
        "diagnostics": {}
    }
    
    # 1. Test connection (instruction)
    report["diagnostics"]["connection_test"] = test_connection(host, user, port, timeout=timeout)
    
    # 2. Network tests
    report["diagnostics"]["network"] = test_network(host, mtr_count=mtr_count, timeout=timeout)
    
    # 3. Server logs (if on server)
    report["diagnostics"]["server_logs"] = check_server_logs(log_lines=log_lines, timeout=timeout)
    
    # 4. Keepalive config
    report["diagnostics"]["keepalive"] = check_keepalive_config(timeout=timeout)
    
    # 5. Firewall
    report["diagnostics"]["firewall"] = check_firewall(timeout=timeout)
    
    # 6. Fail2ban
    report["diagnostics"]["fail2ban"] = check_fail2ban(timeout=timeout)
    
    # 7. Server load
    report["diagnostics"]["server_load"] = check_server_load(timeout=timeout)
    
    # 8. Generate config
    report["recommended_ssh_config"] = generate_ssh_config(host, user, port)
    
    # Summary
    report["summary"] = {
        "message": "Diagnostic complet exécuté. Consultez chaque section pour identifier la cause.",
        "common_causes": [
            "1. Timeout NAT/routeur (pas de keepalive) → appliquez la config SSH recommandée",
            "2. Fail2ban a banni votre IP → vérifiez fail2ban sshd jail",
            "3. Serveur surchargé (OOM, CPU 100%) → vérifiez server_load",
            "4. Perte réseau intermédiaire → vérifiez network (MTR)",
            "5. Firewall bloque après X minutes → vérifiez firewall rules"
        ],
        "next_steps": [
            "A. Appliquez la config SSH recommandée (keepalives)",
            "B. Si logs serveur montrent 'timeout preauth' → augmentez LoginGraceTime",
            "C. Si MTR montre pertes réseau → problème ISP/VPN",
            "D. Si fail2ban a banni → débannissez votre IP : sudo fail2ban-client set sshd unbanip VOTRE_IP"
        ]
    }
    
    return report
