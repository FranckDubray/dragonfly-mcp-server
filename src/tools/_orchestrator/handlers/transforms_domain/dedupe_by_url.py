from ..base import AbstractHandler

class DedupeByUrlHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "dedupe_by_url"

    def run(self, new_items, prev_items=None, key="url", **kwargs):
        if prev_items is None:
            prev_items = []
        try:
            seen = set()
            for it in prev_items:
                if isinstance(it, dict) and key in it and it[key]:
                    seen.add(str(it[key]).strip())
            merged = []
            removed = 0
            for it in (new_items or []):
                u = str(it.get(key)).strip() if isinstance(it, dict) else None
                if not u or u in seen:
                    removed += 1
                    continue
                seen.add(u)
                merged.append(it)
            return {"merged": merged, "removed_count": removed}
        except Exception as e:
            raise ValueError(f"dedupe_by_url: invalid inputs ({e})")
