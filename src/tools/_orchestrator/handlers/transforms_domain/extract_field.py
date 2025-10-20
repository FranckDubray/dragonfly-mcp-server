# Transform: extract_field - Extract field from dict/object

from ..base import AbstractHandler, HandlerError

class ExtractFieldHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "extract_field"

    def run(self, data=None, field=None, default=None, **kwargs):
        """
        Extract a field from a dict/object.
        
        Args:
            Dict/object to extract from
            field: Field name (string)
            default: Default value if field not found
        
        Returns:
            {"result": value}
        """
        if data is None:
            return {"result": default}
        
        if not isinstance(data, dict):
            raise HandlerError(
                message=f"extract_field: data must be dict, got {type(data).__name__}",
                code="INVALID_INPUT",
                category="validation",
                retryable=False
            )
        
        if field is None:
            raise HandlerError(
                message="extract_field: field parameter required",
                code="MISSING_PARAM",
                category="validation",
                retryable=False
            )
        
        value = data.get(field, default)
        return {"result": value}
