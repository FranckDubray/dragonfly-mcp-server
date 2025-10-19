from ..base import AbstractHandler, HandlerError

class ExtractFieldHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "extract_field"

    def run(self, data=None, field=None, default=None, **kwargs):
        """Extract field from dict/list using dotted path or index."""
        try:
            if data is None:
                if default is not None:
                    return {"result": default}
                raise HandlerError("data is None and no default", "MISSING_DATA", "validation", False)
            
            if not field:
                return {"result": data}
            
            # Navigate path (e.g., "items.0.title" or "score")
            parts = str(field).split(".")
            current = data
            
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list):
                    try:
                        idx = int(part)
                        current = current[idx] if 0 <= idx < len(current) else None
                    except (ValueError, IndexError):
                        current = None
                else:
                    current = None
                
                if current is None:
                    if default is not None:
                        return {"result": default}
                    raise HandlerError(f"Field '{field}' not found", "FIELD_NOT_FOUND", "validation", False)
            
            return {"result": current}
            
        except HandlerError:
            raise
        except Exception as e:
            raise HandlerError(
                message=f"extract_field failed: {str(e)[:200]}",
                code="EXTRACT_ERROR",
                category="validation",
                retryable=False
            )
