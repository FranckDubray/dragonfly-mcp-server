"""Secure password generation and hashing."""
from __future__ import annotations
import secrets
import string
import logging
from typing import Tuple

from tools._portal_db.utils import run_mysql_via_ssh

LOG = logging.getLogger(__name__)

# Characters for password generation
_LOWER = string.ascii_lowercase
_UPPER = string.ascii_uppercase
_DIGITS = string.digits
_SPECIAL = "!@#$%&*?+-="

_PASSWORD_LENGTH = 16


def generate_password() -> str:
    """Generate a secure random password (16 chars).

    Guarantees at least 2 uppercase, 2 lowercase, 2 digits, 2 special.
    """
    # Mandatory chars
    mandatory = [
        secrets.choice(_UPPER),
        secrets.choice(_UPPER),
        secrets.choice(_LOWER),
        secrets.choice(_LOWER),
        secrets.choice(_DIGITS),
        secrets.choice(_DIGITS),
        secrets.choice(_SPECIAL),
        secrets.choice(_SPECIAL),
    ]

    # Fill remaining
    all_chars = _LOWER + _UPPER + _DIGITS + _SPECIAL
    remaining = _PASSWORD_LENGTH - len(mandatory)
    for _ in range(remaining):
        mandatory.append(secrets.choice(all_chars))

    # Shuffle
    result = list(mandatory)
    secrets.SystemRandom().shuffle(result)
    return "".join(result)


def hash_password_via_php(plain: str) -> Tuple[bool, str]:
    """Hash password using PHP on the remote server (Symfony-compatible).

    Uses password_hash() with bcrypt cost=13 to match existing hashes.

    Returns:
        (success, hash_or_error)
    """
    import subprocess
    import os

    cfg_path = os.getenv(
        "PORTAL_DB_SSH_CONFIG",
        os.path.expanduser(
            "~/Documents/ai-you-web/keys/ssh-users/youssef/config"
        ),
    )
    cfg_cwd = os.getenv(
        "PORTAL_DB_SSH_CWD",
        os.path.expanduser("~/Documents/ai-you-web"),
    )
    ssh_host = os.getenv("PORTAL_DB_SSH_HOST", "front-prod")

    # Escape single quotes in password for PHP
    safe_pw = plain.replace("'", "\\'")

    php_cmd = (
        f"php -r \"echo password_hash('{safe_pw}', PASSWORD_BCRYPT, "
        f"['cost' => 13]);\""
    )

    try:
        result = subprocess.run(
            ["ssh", "-F", cfg_path, ssh_host, php_cmd],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=cfg_cwd,
        )

        if result.returncode != 0:
            return False, f"PHP hash failed: {result.stderr}"

        hashed = result.stdout.strip()
        if not hashed.startswith("$2y$"):
            return False, f"Invalid hash output: {hashed[:20]}"

        return True, hashed

    except subprocess.TimeoutExpired:
        return False, "PHP hash timed out"
    except Exception as e:
        return False, str(e)
