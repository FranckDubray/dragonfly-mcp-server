from ..base import AbstractHandler, HandlerError
from typing import Any, Dict, List, Optional
import re

class TemplateMapHandler(AbstractHandler):
    """
    Map a string template over a list of items, producing an array of strings.

    Features:
      - Supports {{key}} and {{nested.key}} placeholders (dot notation)
      - Optional globals dict merged into each item's context
      - Optional color_map: if item has 'color', inject {{block}} = color_map[color]
      - Optional default_block when color_map is not used
      - Optional round_coords: if item.center.{x,y,z} numeric, round to nearest int

    Inputs:
      - items: list[dict]
      - template: str (e.g., "setblock {{center.x}} {{center.y}} {{center.z}} {{block}}")
      - globals: dict (optional)
      - color_map: dict (optional) e.g., {"light":"white_concrete","dark":"black_concrete"}
      - default_block: str (optional)
      - round_coords: bool (default False)

    Outputs:
      - commands: list[str]
    """

    @property
    def kind(self) -> str:
        return "template_map"

    def run(self, items: Any = None, template: str = "", globals: Optional[Dict[str, Any]] = None,
            color_map: Optional[Dict[str, str]] = None, default_block: Optional[str] = None,
            round_coords: bool = False, **kwargs) -> Dict[str, Any]:
        try:
            arr: List[Any] = items if isinstance(items, list) else []
            if not template:
                return {"commands": []}
            out: List[str] = []
            for it in arr:
                ctx = {}
                if isinstance(globals, dict):
                    ctx.update(globals)
                if isinstance(it, dict):
                    # shallow copy is enough for templating
                    ctx.update(it)
                    # color_map -> block
                    if isinstance(color_map, dict) and "color" in it and isinstance(it.get("color"), str):
                        block = color_map.get(it.get("color"))
                        if block:
                            ctx["block"] = block
                    if "block" not in ctx and default_block:
                        ctx["block"] = default_block
                    if round_coords and isinstance(it.get("center"), dict):
                        c = it["center"]
                        for k in ("x", "y", "z"):
                            v = c.get(k)
                            if isinstance(v, (int, float)):
                                c[k] = int(round(v))
                        ctx["center"] = c
                rendered = self._render(template, ctx)
                out.append(rendered)
            return {"commands": out}
        except Exception as e:
            raise HandlerError(f"template_map failed: {str(e)[:200]}", "TEMPLATE_MAP_ERROR", "validation", False)

    def _render(self, template: str, context: Dict[str, Any]) -> str:
        def repl(match):
            key = match.group(1).strip()
            return str(self._get(context, key) if self._get(context, key) is not None else "")
        return re.sub(r"\{\{\s*([\w\.]+)\s*\}\}", repl, template)

    def _get(self, obj: Any, dotted: str) -> Any:
        cur = obj
        for part in dotted.split('.'):
            if isinstance(cur, dict):
                cur = cur.get(part)
            else:
                return None
        return cur
