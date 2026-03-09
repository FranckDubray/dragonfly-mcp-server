"""Name detection from email addresses."""
from __future__ import annotations
import re
from typing import Tuple


def guess_names(email: str) -> Tuple[str, str]:
    """Guess first_name and last_name from email local part.

    Heuristics:
      prenom.nom@...   → (Prenom, Nom)
      prenom-nom@...   → (Prenom, Nom)
      prenom_nom@...   → (Prenom, Nom)
      prenomnom@...     → (Prenomnom, "")  — can't split reliably

    Returns:
        (first_name, last_name) — capitalized
    """
    local = email.split("@")[0].strip().lower()

    # Remove digits/special at the end (e.g., jean.dupont2@)
    local = re.sub(r"[\d]+$", "", local)

    # Try split by . - _
    for sep in (".", "-", "_"):
        if sep in local:
            parts = [p.strip() for p in local.split(sep) if p.strip()]
            if len(parts) >= 2:
                first = _capitalize(parts[0])
                last = _capitalize(parts[-1])
                return first, last
            elif len(parts) == 1:
                return _capitalize(parts[0]), ""

    # No separator — use whole local part as first name
    return _capitalize(local), ""


def _capitalize(name: str) -> str:
    """Capitalize a name, handling compounds like 'da silva' or 'le roux'."""
    if not name:
        return ""

    # Simple capitalize for single words
    parts = name.split()
    if len(parts) == 1:
        return name.capitalize()

    # For compound names, capitalize each part
    return " ".join(p.capitalize() for p in parts)
