from ..base import AbstractHandler

class FormatTemplateHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "format_template"

    def run(self, template, **kwargs):
        try:
            return {"text": str(template).format(**kwargs)}
        except KeyError as e:
            raise ValueError(f"format_template: missing variable {e}")
