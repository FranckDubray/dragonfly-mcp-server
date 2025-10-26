
# TRANSFORM_META_START
{
  "io_type": "list->list(string)",
  "description": "Convert a list of heterogeneous values to a list of strings (dict/list -> JSON)",
  "inputs": [
    "- items: list[any]"
  ],
  "outputs": [
    "- items: list[string]"
  ]
}
# TRANSFORM_META_END

from ..base import AbstractHandler, HandlerError
import json
from typing import Any, Dict, List

class ToTextListHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "to_text_list"

    def run(self, items=None, **kwargs) -> Dict[str, Any]:
        try:
            arr = items if isinstance(items, list) else []
            out: List[str] = []
            for it in arr:
                if isinstance(it, (dict, list)):
                    try:
                        out.append(json.dumps(it, ensure_ascii=False))
                    except Exception:
                        out.append(str(it))
                else:
                    out.append(str(it))
            return {"items": out}
        except Exception as e:
            raise HandlerError(
                message=f"to_text_list failed: {str(e)[:200]}",
                code="TO_TEXT_LIST_ERROR",
                category="validation",
                retryable=False
            )
