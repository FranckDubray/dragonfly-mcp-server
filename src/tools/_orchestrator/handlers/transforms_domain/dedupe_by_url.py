from ..base import AbstractHandler, HandlerError

class DedupeByUrlHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "dedupe_by_url"

    def run(self, items=None, url_key="url", keep_first=True, **kwargs) -> dict:
        if items is None:
            items = []
        if not isinstance(items, list):
            raise HandlerError(
                message="'items' must be a list of dicts",
                code="INVALID_INPUT",
                category="validation",
                retryable=False
            )
        seen = set()
        out = []
        removed = 0
        for it in items:
            if not isinstance(it, dict):
                # Keep non-dict items untouched
                out.append(it)
                continue
            url = it.get(url_key)
            if not url:
                out.append(it)
                continue
            if url in seen:
                removed += 1
                if not keep_first:
                    # replace previous with current (rare use-case)
                    # find index of previous and replace
                    for i in range(len(out)-1, -1, -1):
                        if isinstance(out[i], dict) and out[i].get(url_key) == url:
                            out[i] = it
                            break
                continue
            seen.add(url)
            out.append(it)
        return {"items": out, "removed": removed, "kept": len(out)}
