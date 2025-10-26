from ..base import AbstractHandler, HandlerError
from typing import Any, Dict, List, Optional
import re

class TemplateMapHandler(AbstractHandler):
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
                    ctx.update(it)
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
