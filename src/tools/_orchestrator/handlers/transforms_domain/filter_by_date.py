# Transform: filter_by_date - Filter items by date field (keep recent only)

from datetime import datetime
from ..base import AbstractHandler, HandlerError

class FilterByDateHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "filter_by_date"

    def run(self, items=None, date_field="published_at", cutoff_iso=None, **kwargs):
        """
        Filter items to keep only those published on or after cutoff date.
        
        Args:
            items: List of items (dicts with date field)
            date_field: Name of date field to check (default: "published_at")
            cutoff_iso: ISO date string (cutoff threshold)
        
        Returns:
            {
                "kept": [...],  # Items >= cutoff
                "dropped": int  # Count of dropped items
            }
        """
        if not items or not isinstance(items, list):
            return {"kept": [], "dropped": 0}
        
        if not cutoff_iso:
            # No cutoff, keep all
            return {"kept": items, "dropped": 0}
        
        try:
            cutoff_dt = datetime.fromisoformat(cutoff_iso.replace('Z', '+00:00'))
        except Exception as e:
            raise HandlerError(
                message=f"Invalid cutoff_iso format: {cutoff_iso}",
                code="INVALID_DATE",
                category="validation",
                retryable=False
            )
        
        kept = []
        dropped = 0
        
        for item in items:
            if not isinstance(item, dict):
                dropped += 1
                continue
            
            date_val = item.get(date_field)
            if not date_val:
                # No date field, drop by default
                dropped += 1
                continue
            
            try:
                # Try parsing date
                if isinstance(date_val, (int, float)):
                    # Unix timestamp
                    item_dt = datetime.fromtimestamp(date_val)
                else:
                    # ISO string
                    date_str = str(date_val).replace('Z', '+00:00')
                    item_dt = datetime.fromisoformat(date_str)
                
                # Compare (keep if >= cutoff)
                if item_dt >= cutoff_dt:
                    kept.append(item)
                else:
                    dropped += 1
            except Exception:
                # Can't parse date, drop
                dropped += 1
        
        return {
            "kept": kept,
            "dropped": dropped
        }
