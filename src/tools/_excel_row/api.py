from __future__ import annotations
import os
import shutil
import time
from typing import Any, Dict
from .validators import validate_basic, validate_position, validate_style_schema
from .utils import safe_join, ROOT
from .core import operate

# Backups now live under docs/office/excel_backups (project-root chroot)
BACKUPS_DIR = os.path.join(ROOT, "docs", "office", "excel_backups")
os.makedirs(BACKUPS_DIR, exist_ok=True)


def _backup_file(abs_path: str, create_backup_flag: bool, safety: bool) -> tuple[list[str], str | None]:
    backups = []
    safety_name = None
    if not os.path.exists(abs_path):
        return backups, safety_name
    ts = time.strftime("%Y%m%d-%H%M%S")
    base = os.path.basename(abs_path)
    if create_backup_flag:
        dst = os.path.join(BACKUPS_DIR, f"{base}.{ts}.bak")
        shutil.copy2(abs_path, dst)
        backups.append(dst)
    if safety:
        dst2 = os.path.join(BACKUPS_DIR, f"{base}.safety.bak")
        shutil.copy2(abs_path, dst2)
        safety_name = dst2
    return backups, safety_name


def _list_backups(file_path: str) -> list[dict]:
    base = os.path.basename(file_path)
    out = []
    if not os.path.isdir(BACKUPS_DIR):
        return out
    for name in os.listdir(BACKUPS_DIR):
        if name.startswith(base + ".") and name.endswith(".bak"):
            out.append({
                "file": os.path.join(BACKUPS_DIR, name),
                "ts": name.split(".")[-2],
            })
    out.sort(key=lambda x: x["ts"], reverse=True)
    return out


def _restore_backup(target_abs: str, version: int = 0) -> dict:
    base = os.path.basename(target_abs)
    backups = _list_backups(base)
    if not backups:
        return {"success": False, "message": "No backups found"}
    ix = min(max(0, version), len(backups) - 1)
    src = backups[ix]["file"]
    shutil.copy2(src, target_abs)
    return {"success": True, "restored_from": src}


def execute_operation(
    operation: str,
    file_path: str,
    sheet_name=None,
    position: int | None = None,
    row_data: Dict[str, Any] | None = None,
    row_format: dict | None = None,
    columns_format: dict | None = None,
    parse: dict | None = None,
    color: str | None = None,
    border_color: str | None = None,
    date_format: str | None = None,
    create_backup_flag: bool = False,
    backup_version: int = 0,
    create_safety_backup: bool = True,
) -> dict:
    # Basic validations
    validate_basic(operation, file_path)
    validate_position(position)
    validate_style_schema(row_format, columns_format)

    # Compatibility mapping (deprecated)
    if color and not (row_format or {}).get("background_color"):
        row_format = dict(row_format or {})
        row_format["background_color"] = color
    if border_color and not ((row_format or {}).get("border") or {}).get("color"):
        row_format = dict(row_format or {})
        b = dict((row_format.get("border") or {}))
        b.setdefault("style", "thin")
        b["color"] = border_color
        row_format["border"] = b
    if date_format and not ((parse or {}).get("date_input_format")):
        parse = dict(parse or {})
        parse["date_input_format"] = date_format

    abs_path = safe_join(file_path)

    if operation == "list_backups":
        return {"success": True, "operation": operation, "file_path": file_path, "backups": _list_backups(file_path)}

    if operation == "restore_backup":
        res = _restore_backup(abs_path, version=backup_version)
        res.update({"operation": operation, "file_path": file_path})
        return res

    # Pre-modification backups
    created, safety = _backup_file(abs_path, create_backup_flag, create_safety_backup)

    result = operate(
        operation=operation,
        file_path=abs_path,
        sheet_name=sheet_name,
        position=position,
        row_data=row_data,
        row_format=row_format,
        columns_format=columns_format,
        parse=parse,
    )

    result.update({
        "file_path": file_path,
        "backups_created": len(created),
        "safety_backup": bool(safety),
        "backups_dir": BACKUPS_DIR,
    })
    return result
