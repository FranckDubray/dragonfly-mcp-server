from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# Project root and .env management
# ----------------------------------------------------------------------------

def find_project_root() -> Path:
    """Detect project root (folder containing pyproject.toml or .git or src)."""
    cur = Path.cwd()
    try:
        while True:
            if (cur / 'pyproject.toml').exists() or (cur / '.git').exists():
                return cur
            # Heuristic: if running from src/, the parent that contains 'src' is the root
            if (cur / 'src').exists() and (cur != cur.parent):
                if cur.name == 'src':
                    return cur.parent
                else:
                    return cur
            if cur == cur.parent:
                return Path.cwd()
            cur = cur.parent
    except Exception:
        return Path.cwd()

PROJECT_ROOT = find_project_root()
ENV_FILE = PROJECT_ROOT / '.env'
GITIGNORE_FILE = PROJECT_ROOT / '.gitignore'


def mask_secret(secret: Optional[str]) -> str:
    if not secret:
        return ''
    try:
        if len(secret) <= 8:
            return '***' + secret[-2:]
        return '*' * (len(secret) - 4) + secret[-4:]
    except Exception:
        return '***'


def load_env_file() -> None:
    """Load .env into os.environ if present."""
    if not ENV_FILE.exists():
        logger.info(f"No .env file at {ENV_FILE} (will be created on save)")
        return
    try:
        for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, val = line.split('=', 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            os.environ[key] = val
        logger.info("Loaded environment variables from .env")
    except Exception as e:
        logger.warning(f"Failed to load .env: {e}")


def _read_env_dict() -> Dict[str, str]:
    data: Dict[str, str] = {}
    if ENV_FILE.exists():
        try:
            for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                k, v = line.split('=', 1)
                data[k.strip()] = v.strip()
        except Exception as e:
            logger.warning(f"Could not parse existing .env: {e}")
    return data


def _write_env_dict(d: Dict[str, str]) -> None:
    lines = [f"{k}={v}" for k, v in d.items()]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding='utf-8')
    logger.info(f"Saved {len(d)} keys to {ENV_FILE}")


def _ensure_env_gitignore():
    try:
        if GITIGNORE_FILE.exists():
            gi = GITIGNORE_FILE.read_text(encoding='utf-8')
            lines = [ln.strip() for ln in gi.splitlines()]
            if '.env' not in lines:
                with GITIGNORE_FILE.open('a', encoding='utf-8') as f:
                    f.write('\n# Local environment\n.env\n')
                logger.info("Added .env to .gitignore")
        else:
            GITIGNORE_FILE.write_text('# Git ignore\n.env\n', encoding='utf-8')
            logger.info("Created .gitignore with .env entry")
    except Exception as e:
        logger.warning(f"Failed to ensure .env in .gitignore: {e}")


def save_env_vars(updates: Dict[str, Optional[str]]) -> Dict[str, Any]:
    updates_clean = {k: v for k, v in updates.items() if isinstance(v, str) and v.strip() != ''}
    if not updates_clean:
        return {"updated": 0, "message": "No values provided"}

    for k, v in updates_clean.items():
        os.environ[k] = v

    env_dict = _read_env_dict()
    env_dict.update(updates_clean)
    _write_env_dict(env_dict)
    _ensure_env_gitignore()

    summary = {k: mask_secret(v) for k, v in updates_clean.items()}
    return {"updated": len(updates_clean), "masked": summary, "env_file": str(ENV_FILE)}
