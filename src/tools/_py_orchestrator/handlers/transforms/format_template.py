# TRANSFORM_META_START
{
  "io_type": "object->string",
  "description": "Format a template string with context variables (supports {{key}} and {key})",
  "inputs": [
    "- template: string with {{key}} or {key} placeholders",
    "- context: object"
  ],
  "outputs": [
    "- result: string"
  ]
}
# TRANSFORM_META_END

from ..base import AbstractHandler, HandlerError
from typing import Any, Dict
import re

class FormatTemplateHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "format_template"

    def run(self, template: str = "", context: Dict[str, Any] | None = None, **kwargs) -> dict:
        try:
            if not isinstance(template, str):
                template = str(template)
            ctx = context if isinstance(context, dict) else {}
            # Two-pass: first {{key}}, then {key}
            def get(d: Dict[str, Any], path: str):
                cur: Any = d
                for part in path.split('.'):
                    if isinstance(cur, dict) and part in cur:
                        cur = cur[part]
                    else:
                        return ""
                return cur if cur is not None else ""

            # Replace {{ key }} with values (dot notation allowed)
            def repl_double(m):
                key = m.group(1).strip()
                return str(get(ctx, key))

            out = re.sub(r"\{\{\s*([\w\.]+)\s*\}\}", repl_double, template)

            # Replace {KEY} tokens (flat keys, no dot) — conservative to avoid f-string like braces
            # Accept letters, digits, underscore only
            def repl_single(m):
                key = m.group(1)
                if '.' in key:
                    return m.group(0)  # do not resolve dot here to avoid collision with other uses
                return str(ctx.get(key, m.group(0)))

            out = re.sub(r"\{([A-Za-z0-9_]+)\}", repl_single, out)
            return {"result": out}
        except Exception as e:
            raise HandlerError(
                message=f"format_template failed: {str(e)[:200]}",
                code="FORMAT_TEMPLATE_ERROR",
                category="validation",
                retryable=False,
            )
