# TRANSFORM_META_START
{
  "io_type": "list->list",
  "description": "Concatenate multiple lists into one flat list",
  "inputs": [
    "- lists: list[list[any]]"
  ],
  "outputs": [
    "- items: list[any]"
  ]
}
# TRANSFORM_META_END



# Transform: array_concat — concatenate multiple lists into one flat list
# JSON in → JSON out, no I/O. <1KB

from typing import Any, Dict, List
from ..base import AbstractHandler, HandlerError

class ArrayConcatHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "array_concat"

    def run(self, lists: List[Any] = None, **kwargs) -> Dict:
        try:
            out: List[Any] = []
            for lst in (lists or []):
                if isinstance(lst, list):
                    out.extend(lst)
                elif lst is None:
                    continue
                else:
                    raise HandlerError("array_concat expects lists", "INVALID_INPUT", "validation", False)
            return {"items": out}
        except HandlerError:
            raise
        except Exception as e:
            raise HandlerError(f"array_concat failed: {str(e)[:180]}", "ARRAY_CONCAT_ERROR", "validation", False)
