from ..base import AbstractHandler

class SetValueHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "set_value"

    def run(self, value=None, **kwargs):
        return {"result": value}
