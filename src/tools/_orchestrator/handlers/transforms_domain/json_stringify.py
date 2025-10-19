import json
from ..base import AbstractHandler

class JsonStringifyHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "json_stringify"

    def run(self, value, ensure_ascii=False, indent=None, **kwargs):
        try:
            s = json.dumps(value, ensure_ascii=ensure_ascii, indent=indent)
            return {"json_string": s, "length": len(s)}
        except Exception as e:
            raise ValueError(f"json_stringify: cannot stringify ({e})")
