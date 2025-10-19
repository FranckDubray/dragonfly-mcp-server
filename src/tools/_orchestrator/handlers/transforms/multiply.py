from ..base import AbstractHandler, HandlerError

class MultiplyHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "multiply"

    def run(self, a=0, b=1, **kwargs):
        try:
            if a is None:
                a = 0
            if b is None:
                b = 1
            return {"result": float(a) * float(b)}
        except Exception as e:
            raise HandlerError(
                message=f"multiply: invalid inputs ({e})",
                code="INVALID_INPUT",
                category="validation",
                retryable=False
            )
