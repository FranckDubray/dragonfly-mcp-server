from __future__ import annotations
from typing import Optional, Dict, Any
from openpyxl.cell import Cell
from .styles import build_font, build_alignment, build_fill, build_border
from .number_formats import resolve_number_format


class StyleBundle:
    def __init__(self, cfg: Optional[dict] = None):
        self.cfg = cfg or {}
        self.font = build_font(self.cfg.get("font"))
        self.alignment = build_alignment(self.cfg.get("alignment"))
        self.fill = build_fill(self.cfg)
        nf_cfg = self.cfg.get("number_format") or {}
        self.number_format = resolve_number_format(
            nf_cfg.get("preset"), nf_cfg.get("custom"), nf_cfg
        )
        self.border = build_border(self.cfg.get("border"))

    def apply_to_cell(self, cell: Cell):
        if self.number_format:
            cell.number_format = self.number_format
        if self.font:
            cell.font = self.font
        if self.alignment:
            cell.alignment = self.alignment
        if self.fill:
            cell.fill = self.fill
        if self.border:
            cell.border = self.border


def build_style_bundle(cfg: Optional[dict]) -> StyleBundle | None:
    if not cfg:
        return None
    return StyleBundle(cfg)


def apply_row_style(cells: list[Cell], row_style: Optional[StyleBundle]):
    if not row_style:
        return
    for c in cells:
        row_style.apply_to_cell(c)


def apply_per_column_styles(cells_by_name: Dict[str, Cell], per_col_cfg: Dict[str, dict] | None, header_map: Dict[str, str]):
    if not per_col_cfg:
        return
    # header_map: normalized_name -> real header
    for key, cfg in per_col_cfg.items():
        # try direct match (real header) then normalized
        cell = cells_by_name.get(key)
        if not cell and key in header_map:
            real = header_map[key]
            cell = cells_by_name.get(real)
        if not cell:
            continue
        sb = build_style_bundle(cfg)
        if sb:
            sb.apply_to_cell(cell)
