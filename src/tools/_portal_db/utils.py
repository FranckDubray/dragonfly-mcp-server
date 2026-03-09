"""Configuration and helpers for Portal DB."""
from __future__ import annotations
import os
import subprocess
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

LOG = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SSH + MySQL configuration from environment
# ---------------------------------------------------------------------------

def get_config() -> Dict[str, str]:
    """Load portal DB config from environment."""
    return {
        "ssh_config": os.getenv(
            "PORTAL_DB_SSH_CONFIG",
            os.path.expanduser(
                "~/Documents/ai-you-web/keys/ssh-users/youssef/config"
            ),
        ),
        "ssh_cwd": os.getenv(
            "PORTAL_DB_SSH_CWD",
            os.path.expanduser("~/Documents/ai-you-web"),
        ),
        "ssh_host": os.getenv("PORTAL_DB_SSH_HOST", "front-prod"),
        "mysql_host": os.getenv("PORTAL_DB_MYSQL_HOST", "db-prod"),
        "mysql_user": os.getenv("PORTAL_DB_MYSQL_USER", "symfony_user"),
        "mysql_password": os.getenv("PORTAL_DB_MYSQL_PASSWORD", ""),
        "mysql_db": os.getenv("PORTAL_DB_MYSQL_DB", "appwebldragonfly"),
    }


def _mask(password: str) -> str:
    """Mask password for logging."""
    if not password:
        return ""
    return "****" + password[-2:] if len(password) > 4 else "****"


# ---------------------------------------------------------------------------
# Execute MySQL query via SSH
# ---------------------------------------------------------------------------

def run_mysql_via_ssh(
    sql: str,
    timeout: int = 30,
    output_format: str = "tsv",
) -> Dict[str, Any]:
    """Execute a MySQL command via SSH and return raw stdout.

    Args:
        sql: SQL query to execute.
        timeout: Max seconds.
        output_format: "tsv" (default, -B) or "xml" (--xml, for multiline fields).

    Returns:
        {"success": True, "stdout": "...", "stderr": "..."} or
        {"success": False, "error": "..."}
    """
    cfg = get_config()

    if not cfg["mysql_password"]:
        return {
            "success": False,
            "error": "PORTAL_DB_MYSQL_PASSWORD not configured in .env",
        }

    # Escape single quotes in SQL for shell
    safe_sql = sql.replace("'", "'\\''")

    fmt_flag = "--xml" if output_format == "xml" else "-B"

    mysql_cmd = (
        f"mysql -h {cfg['mysql_host']} "
        f"-u {cfg['mysql_user']} "
        f"-p'{cfg['mysql_password']}' "
        f"{cfg['mysql_db']} "
        f"{fmt_flag} -e '{safe_sql}'"
    )

    ssh_cmd = [
        "ssh", "-F", cfg["ssh_config"],
        cfg["ssh_host"],
        mysql_cmd,
    ]

    LOG.info("🔍 Portal DB query via SSH → %s", cfg["ssh_host"])
    LOG.debug("SQL: %s", sql[:200])

    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cfg["ssh_cwd"],
        )

        # Filter out MySQL password warning from stderr
        stderr = result.stderr
        if stderr:
            stderr = "\n".join(
                line for line in stderr.splitlines()
                if "Using a password on the command line" not in line
            ).strip()

        if result.returncode != 0:
            LOG.warning("❌ MySQL error: %s", stderr)
            return {"success": False, "error": stderr or "Unknown MySQL error"}

        return {"success": True, "stdout": result.stdout, "stderr": stderr}

    except subprocess.TimeoutExpired:
        LOG.error("⏱️ Query timed out after %ds", timeout)
        return {"success": False, "error": f"Query timed out after {timeout}s"}
    except FileNotFoundError:
        LOG.error("❌ SSH binary not found or config missing")
        return {
            "success": False,
            "error": (
                "SSH config not found. Check PORTAL_DB_SSH_CONFIG "
                "and PORTAL_DB_SSH_CWD in .env"
            ),
        }
    except Exception as e:
        LOG.error("💥 Unexpected error: %s", e)
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Parse tab-separated MySQL output into list of dicts
# ---------------------------------------------------------------------------

def parse_tsv(raw: str) -> Dict[str, Any]:
    """Parse MySQL -B output (tab-separated) into structured data.

    Returns:
        {"columns": [...], "rows": [{...}, ...], "returned_count": N}
    """
    if not raw or not raw.strip():
        return {"columns": [], "rows": [], "returned_count": 0}

    lines = raw.strip().split("\n")
    if len(lines) < 1:
        return {"columns": [], "rows": [], "returned_count": 0}

    columns = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        values = line.split("\t")
        row = {}
        for i, col in enumerate(columns):
            val = values[i] if i < len(values) else None
            # Try to convert numeric values
            if val is not None and val != "NULL":
                try:
                    val = int(val)
                except ValueError:
                    try:
                        val = float(val)
                    except ValueError:
                        pass
            elif val == "NULL":
                val = None
            row[col] = val
        rows.append(row)

    return {
        "columns": columns,
        "rows": rows,
        "returned_count": len(rows),
    }


# ---------------------------------------------------------------------------
# Parse XML MySQL output into list of dicts (handles multiline fields)
# ---------------------------------------------------------------------------

def parse_xml(raw: str) -> Dict[str, Any]:
    """Parse MySQL --xml output into structured data.

    Handles multiline field values (newlines inside JSON columns).

    Returns:
        {"columns": [...], "rows": [{...}, ...], "returned_count": N}
    """
    if not raw or not raw.strip():
        return {"columns": [], "rows": [], "returned_count": 0}

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        LOG.error("XML parse error: %s", e)
        return {"columns": [], "rows": [], "returned_count": 0}

    rows = []
    columns = []
    for row_el in root.findall("row"):
        row = {}
        for field in row_el.findall("field"):
            col_name = field.get("name")
            if col_name and col_name not in columns:
                columns.append(col_name)

            # xsi:nil="true" means NULL
            val = field.text
            if val is None:
                row[col_name] = None
                continue

            # Try to convert numeric values
            try:
                val = int(val)
            except ValueError:
                try:
                    val = float(val)
                except ValueError:
                    pass
            row[col_name] = val
        rows.append(row)

    return {
        "columns": columns,
        "rows": rows,
        "returned_count": len(rows),
    }
