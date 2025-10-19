from datetime import datetime, timezone
from ..base import AbstractHandler, HandlerError

class FilterByDateHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "filter_by_date"

    def run(self, items=None, date_field="published_at", cutoff_iso=None, **kwargs):
        """Filter items by date field (keep only >= cutoff)."""
        try:
            if not items:
                return {"kept": [], "dropped": []}
            
            if not cutoff_iso:
                # No filter, return all
                return {"kept": items, "dropped": []}
            
            # Parse cutoff
            try:
                cutoff_dt = datetime.fromisoformat(cutoff_iso.replace("Z", "+00:00"))
            except Exception as e:
                raise HandlerError(f"Invalid cutoff_iso: {e}", "INVALID_CUTOFF", "validation", False)
            
            kept = []
            dropped = []
            
            for item in items:
                if not isinstance(item, dict):
                    dropped.append(item)
                    continue
                
                date_str = item.get(date_field)
                if not date_str:
                    dropped.append(item)
                    continue
                
                try:
                    # Parse item date
                    item_dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
                    
                    if item_dt >= cutoff_dt:
                        kept.append(item)
                    else:
                        dropped.append(item)
                except Exception:
                    # Invalid date → drop
                    dropped.append(item)
            
            return {"kept": kept, "dropped": dropped}
            
        except HandlerError:
            raise
        except Exception as e:
            raise HandlerError(
                message=f"filter_by_date failed: {str(e)[:200]}",
                code="FILTER_ERROR",
                category="validation",
                retryable=False
            )
