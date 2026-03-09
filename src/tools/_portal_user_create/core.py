"""Core logic for portal user creation."""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from tools._portal_db.utils import run_mysql_via_ssh, parse_tsv
from .names import guess_names
from .password import generate_password, hash_password_via_php

LOG = logging.getLogger(__name__)

_MAX_BATCH = 50
_ROLE = '["ROLE_USER"]'  # HARDCODED — NEVER admin


def _query(sql: str) -> Dict[str, Any]:
    """Helper to run read query."""
    r = run_mysql_via_ssh(sql, timeout=30)
    if not r["success"]:
        return {"error": r["error"]}
    return parse_tsv(r["stdout"])


def _write(sql: str) -> Dict[str, Any]:
    """Helper to run write query."""
    r = run_mysql_via_ssh(sql, timeout=30)
    if not r["success"]:
        return {"error": r["error"]}
    return {"success": True}


def list_companies(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """List available companies."""
    count_r = _query("SELECT COUNT(*) as total FROM company")
    total = 0
    if "rows" in count_r and count_r["rows"]:
        total = count_r["rows"][0].get("total", 0)

    r = _query(
        f"SELECT c.id, c.name, c.tenant_id, t.name as tenant_name "
        f"FROM company c JOIN tenant t ON c.tenant_id = t.id "
        f"ORDER BY c.name LIMIT {limit} OFFSET {offset}"
    )
    if "error" in r:
        return r

    return {
        "companies": r.get("rows", []),
        "returned_count": r.get("returned_count", 0),
        "total_count": total,
        "has_more": (offset + r.get("returned_count", 0)) < total,
    }


def _validate_company(company_id: int) -> Optional[Dict[str, Any]]:
    """Validate company exists. Returns company info or None."""
    r = _query(
        f"SELECT c.id, c.name, c.tenant_id, t.name as tenant_name "
        f"FROM company c JOIN tenant t ON c.tenant_id = t.id "
        f"WHERE c.id = {company_id}"
    )
    if "error" in r or not r.get("rows"):
        return None
    return r["rows"][0]


def _check_existing_emails(emails: List[str]) -> List[str]:
    """Return emails that already exist in the database."""
    if not emails:
        return []
    quoted = ",".join(f"'{e}'" for e in emails)
    r = _query(f"SELECT email FROM user WHERE email IN ({quoted})")
    if "error" in r:
        return []
    return [row["email"] for row in r.get("rows", [])]


def _prepare_users(
    users_input: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """Prepare user list: fill in missing names from email."""
    prepared = []
    for u in users_input:
        email = u["email"].strip().lower()
        first = u.get("first_name", "").strip()
        last = u.get("last_name", "").strip()

        if not first or not last:
            guessed_first, guessed_last = guess_names(email)
            if not first:
                first = guessed_first
            if not last:
                last = guessed_last

        prepared.append({
            "email": email,
            "first_name": first,
            "last_name": last,
        })
    return prepared


def preview(
    company_id: int,
    users_input: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Preview user creation — dry run."""
    if len(users_input) > _MAX_BATCH:
        return {"error": f"Max {_MAX_BATCH} users per batch"}

    # Validate company
    company = _validate_company(company_id)
    if not company:
        return {"error": f"Company {company_id} not found"}

    # Prepare names
    prepared = _prepare_users(users_input)

    # Check duplicates
    emails = [u["email"] for u in prepared]
    existing = _check_existing_emails(emails)

    users_preview = []
    for u in prepared:
        status = "duplicate" if u["email"] in existing else "ready"
        users_preview.append({**u, "status": status})

    ready = sum(1 for u in users_preview if u["status"] == "ready")
    dupes = sum(1 for u in users_preview if u["status"] == "duplicate")

    return {
        "dry_run": True,
        "company": company,
        "users": users_preview,
        "ready_count": ready,
        "duplicate_count": dupes,
        "total_count": len(users_preview),
    }


def execute(
    company_id: int,
    users_input: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Create users in database. Returns credentials ONCE."""
    if len(users_input) > _MAX_BATCH:
        return {"error": f"Max {_MAX_BATCH} users per batch"}

    # Validate company
    company = _validate_company(company_id)
    if not company:
        return {"error": f"Company {company_id} not found"}

    # Prepare
    prepared = _prepare_users(users_input)
    emails = [u["email"] for u in prepared]
    existing = _check_existing_emails(emails)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    credentials = []
    created = 0
    skipped = []
    errors = []

    for u in prepared:
        if u["email"] in existing:
            skipped.append(u["email"])
            continue

        # Generate password
        plain_pw = generate_password()
        ok, hashed = hash_password_via_php(plain_pw)
        if not ok:
            errors.append({"email": u["email"], "error": hashed})
            continue

        # Escape strings for SQL
        e_email = u["email"].replace("'", "\\'")
        e_first = u["first_name"].replace("'", "\\'")
        e_last = u["last_name"].replace("'", "\\'")
        e_hash = hashed.replace("'", "\\'")

        sql = (
            f"INSERT INTO user "
            f"(email, roles, password, first_name, last_name, "
            f"company_id, create_at, is_active, is_locked, "
            f"failed_login_attempts, total_kwh_cost, "
            f"is_mcp_enabled, mcp_port) "
            f"VALUES ("
            f"'{e_email}', '{_ROLE}', '{e_hash}', "
            f"'{e_first}', '{e_last}', "
            f"{company_id}, '{now}', 1, 0, "
            f"0, 0, 0, 2042)"
        )

        result = _write(sql)
        if "error" in result:
            errors.append({"email": u["email"], "error": result["error"]})
            continue

        credentials.append({
            "email": u["email"],
            "first_name": u["first_name"],
            "last_name": u["last_name"],
            "password": plain_pw,
        })
        created += 1

    LOG.info(
        "✅ Created %d users for %s (skipped: %d, errors: %d)",
        created, company.get("name"), len(skipped), len(errors),
    )

    result = {
        "created_count": created,
        "company": company,
        "credentials": credentials,
    }
    if skipped:
        result["skipped_duplicates"] = skipped
    if errors:
        result["errors"] = errors

    return result
