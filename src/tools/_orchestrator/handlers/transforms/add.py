from ..base import AbstractHandler, HandlerError

class AddHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "add"

    def run(self, a=0, b=0, **kwargs):
        try:
            if a is None:
                a = 0
            if b is None:
                b = 0
            if isinstance(a, (int, float)) or isinstance(b, (int, float)):
                return {"result": float(a) + float(b)}
            return {"result": float(a) + float(b)}
        except Exception as e:
            raise HandlerError(
                message=f"add: invalid inputs ({e})",
                code="INVALID_INPUT",
                category="validation",
                retryable=False
            )
