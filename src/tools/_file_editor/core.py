"""Core — re-exports all operations from ops_read and ops_write.

This module exists for backward compatibility with api.py imports.
All logic lives in ops_read.py and ops_write.py.
"""
from .ops_read import op_list, op_versions, op_diff      # noqa: F401
from .ops_write import (                                   # noqa: F401
    op_create, op_edit, op_append, op_delete, op_restore,
)

__all__ = [
    "op_list", "op_versions", "op_diff",
    "op_create", "op_edit", "op_append", "op_delete", "op_restore",
]
