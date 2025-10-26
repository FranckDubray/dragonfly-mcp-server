import re
from ..base import AbstractHandler, HandlerError

class FormatTemplateHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "format_template"

    def run(self, template=None, context=None, **kwargs):
        if not template:
            return {"result": ""}
        if not context or not isinstance(context, dict):
            context = {}
        try:
            def replacer(match):
                key = match.group(1)
                # Support dotted paths a.b.c
                val = self._get(context, key)
                return str(val if val is not None else "")
            result = re.sub(r"\{\{([\w\.]+)\}\}", replacer, template)
            return {"result": result}
        except Exception as e:
            raise HandlerError(
                message=f"format_template failed: {str(e)[:200]}",
                code="TEMPLATE_ERROR",
                category="validation",
                retryable=False
            )

    def _get(self, obj, dotted):
        cur = obj
        for part in str(dotted).split('.'):
            if isinstance(cur, dict):
                cur = cur.get(part)
            else:
                return None
        return cur
