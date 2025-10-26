# TRANSFORM_META_START
{
  "io_type": "number(s)->number",
  "description": "Generic arithmetic operations (add, sub, mul, div, inc, dec)",
  "inputs": [
    "- op: string (add|sub|mul|div|inc|dec)",
    "- a: number (optional for inc/dec)",
    "- b: number (when op=add|sub|mul|div)",
    "- step: number (when op=inc|dec; default 1)",
    "- default: number (fallback when input invalid)",
    "- safe_div_zero: boolean (default true; if true -> return default)"
  ],
  "outputs": [
    "- result: number"
  ]
}
# TRANSFORM_META_END

from ..base import AbstractHandler, HandlerError

class ArithmeticHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "arithmetic"

    def run(self, op: str = None, a=None, b=None, step=1, default=0, safe_div_zero=True, **kwargs):
        try:
            op = (op or "").lower().strip()
            if op not in {"add","sub","mul","div","inc","dec"}:
                raise HandlerError("arithmetic: invalid op", "INVALID_OP", "validation", False)
            # parse numbers
            def num(x, d=0):
                try:
                    return float(x)
                except Exception:
                    return float(d)
            if op in {"inc","dec"}:
                av = num(a, default)
                sv = num(step, 1)
                res = av + sv if op == "inc" else av - sv
                return {"result": res}
            # binary ops
            av = num(a, default)
            bv = num(b, default)
            if op == "add":
                return {"result": av + bv}
            if op == "sub":
                return {"result": av - bv}
            if op == "mul":
                return {"result": av * bv}
            if op == "div":
                if bv == 0:
                    if safe_div_zero:
                        return {"result": num(default, 0)}
                    raise HandlerError("division by zero", "DIV_ZERO", "validation", False)
                return {"result": av / bv}
        except HandlerError:
            raise
        except Exception as e:
            raise HandlerError(f"arithmetic failed: {str(e)[:180]}", "ARITH_ERROR", "validation", False)
