























from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path

# List files under docs/images (for avatar picker)

IMG_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}

async def list_avatars() -> Dict[str, Any]:
    try:
        from config import find_project_root
        root = Path(find_project_root())
    except Exception:
        root = Path.cwd()
    base = root / 'docs' / 'images'
    if not base.exists():
        return {"accepted": True, "status": "ok", "images": []}
    items: List[str] = []
    try:
        for p in sorted(base.iterdir()):
            if p.is_file() and p.suffix.lower() in IMG_EXTS:
                items.append(p.name)
    except Exception:
        pass
    return {"accepted": True, "status": "ok", "images": items}
