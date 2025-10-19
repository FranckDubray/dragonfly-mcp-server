import json
from ..base import AbstractHandler, HandlerError

class JsonStringifyHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "json_stringify"

    def run(self, value=None, **kwargs):
        try:
            return {"json_string": json.dumps(value, ensure_ascii=False)}
        except Exception as e:
            raise HandlerError(
                message=f"json_stringify failed: {e}",
                code="INVALID_INPUT",
                category="validation",
                retryable=False
            )
