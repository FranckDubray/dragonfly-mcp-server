# Transform: format_template - Format string template with context vars

import re
from ..base import AbstractHandler, HandlerError

class FormatTemplateHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "format_template"

    def run(self, template=None, context=None, **kwargs):
        """
        Format a template string with context variables.
        
        Uses {{varname}} syntax (not ${} to avoid conflict with orchestrator resolution).
        
        Args:
            template: Template string with {{key}} placeholders
            context: Dict of variables to substitute
        
        Returns:
            {"result": formatted_string}
        
        Example:
            template: "Score: {{score}}/10 | Attempts: {{count}}"
            context: {"score": 7.5, "count": 2}
            result: "Score: 7.5/10 | Attempts: 2"
        """
        if not template:
            return {"result": ""}
        
        if not context or not isinstance(context, dict):
            context = {}
        
        try:
            # Replace {{key}} with context[key]
            def replacer(match):
                key = match.group(1)
                value = context.get(key, f"{{{{key}}}}")  # Keep original if not found
                return str(value)
            
            result = re.sub(r'\{\{(\w+)\}\}', replacer, template)
            return {"result": result}
        
        except Exception as e:
            raise HandlerError(
                message=f"format_template failed: {str(e)[:200]}",
                code="TEMPLATE_ERROR",
                category="validation",
                retryable=False
            )
