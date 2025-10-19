import json
from ..base import AbstractHandler, HandlerError

class JsonStringifyHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "json_stringify"

    def run(self, value, ensure_ascii=False, indent=None, **kwargs) -> dict:
        try:
            json_str = json.dumps(value, ensure_ascii=ensure_ascii, indent=indent)
            return {"json_string": json_str, "length": len(json_str)}
        except (TypeError, ValueError) as e:
            raise HandlerError(
                message=f"Cannot stringify to JSON: {str(e)[:200]}",
                code="JSON_STRINGIFY_ERROR",
                category="validation",
                retryable=False
            )
