from ..base import AbstractHandler

class DecrementHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "decrement"

    def run(self, value=0, step=1, **kwargs):
        try:
            if value is None:
                value = 0
            if isinstance(value, (int, float)) or isinstance(step, (int, float)):
                return {"result": (float(value) - float(step)) if any(isinstance(x, float) for x in (value, step)) else int(value) - int(step)}
            v = float(value)
            s = float(step)
            r = v - s
            return {"result": r if (isinstance(value, float) or isinstance(step, float)) else int(r)}
        except Exception as e:
            raise ValueError(f"decrement: invalid inputs ({e})")
