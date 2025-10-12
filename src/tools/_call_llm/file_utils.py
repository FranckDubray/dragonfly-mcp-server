"""
Compatibility wrappers for image utilities expected by call_llm.py.
Exports:
- _file_to_data_url(path) -> (data_url|None, diag)
- _image_part_from_url(url) -> dict (OpenAI content part)
"""
from __future__ import annotations
from typing import Any, Dict, Tuple

from .utils_images import file_to_data_url, image_part_from_url


def _file_to_data_url(path: str) -> Tuple[str | None, Dict[str, Any]]:
    return file_to_data_url(path)


def _image_part_from_url(u: str) -> Dict[str, Any]:
    return image_part_from_url(u)
