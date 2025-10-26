# TRANSFORM_META_START
{
  "io_type": "any->any",
  "description": "Set/forward a scalar JSON-serializable value",
  "inputs": [
    "- value: any"
  ],
  "outputs": [
    "- result: any"
  ]
}
# TRANSFORM_META_END

from ..base import AbstractHandler, HandlerError

class SetValueHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "set_value"

    def run(self, value=None, **kwargs) -> dict:
        try:
            return {"result": value}
        except Exception as e:
            raise HandlerError(
                message=f"set_value failed: {str(e)[:200]}",
                code="SET_VALUE_ERROR",
                category="validation",
                retryable=False,
            )
