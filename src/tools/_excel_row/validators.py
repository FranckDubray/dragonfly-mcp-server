from __future__ import annotations
from typing import Any, Dict
import re

COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def validate_basic(operation: str, file_path: str):
    if operation not in {"insert_row", "update_row", "delete_row", "list_backups", "restore_backup"}:
        raise ValueError("Invalid operation")
    if not file_path.lower().endswith(".xlsx"):
        raise ValueError("file_path must be .xlsx")


def validate_position(pos: int | None):
    if pos is None:
        return
    if pos < 1:
        raise ValueError("position must be >= 1")


def validate_color_hex(c: str | None):
    if c is None:
        return
    if not COLOR_RE.match(c):
        raise ValueError(f"Invalid color hex: {c}")


def validate_style_schema(row_format: Dict[str, Any] | None, columns_format: Dict[str, Any] | None):
    # Minimal validation; deep validation is handled when building styles.
    if row_format:
        validate_color_hex(row_format.get("background_color"))
        b = row_format.get("border") or {}
        validate_color_hex(b.get("color"))
        f = row_format.get("font") or {}
        validate_color_hex(f.get("color"))
    if columns_format:
        for k, v in columns_format.items():
            if not isinstance(v, dict):
                raise ValueError(f"columns_format.{k} must be object")
            validate_color_hex(v.get("background_color"))
            b = (v.get("border") or {})
            validate_color_hex(b.get("color"))
            f = (v.get("font") or {})
            validate_color_hex(f.get("color"))
