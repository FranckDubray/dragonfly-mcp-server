import re
from ..base import AbstractHandler, HandlerError

class FormatTemplateHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "format_template"

    def run(self, template=None, context=None, **kwargs):
        """Simple template formatting with ${key} syntax."""
        try:
            if not template:
                return {"result": ""}
            
            if not context:
                context = {}
            
            result = str(template)
            
            # Replace ${key} with context[key]
            pattern = re.compile(r'\$\{([^}]+)\}')
            
            def replacer(match):
                key = match.group(1)
                if key in context:
                    return str(context[key])
                return match.group(0)  # Leave unchanged if not found
            
            result = pattern.sub(replacer, result)
            
            return {"result": result}
            
        except Exception as e:
            raise HandlerError(
                message=f"format_template failed: {str(e)[:200]}",
                code="FORMAT_ERROR",
                category="validation",
                retryable=False
            )
