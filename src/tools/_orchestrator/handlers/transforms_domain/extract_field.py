from ..base import AbstractHandler

class ExtractFieldHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "extract_field"

    def run(self, data, path=None, paths=None, default=None, **kwargs):
        if path is None and paths is None:
            raise ValueError("extract_field: either 'path' or 'paths' must be specified")
        if not isinstance(data, (dict, list)):
            return {"value": default} if path else {k: default for k in paths.keys()}
        if path:
            return {"value": self._extract_single(data, path, default)}
        result = {}
        for out_key, p in paths.items():
            result[out_key] = self._extract_single(data, p, default)
        return result

    def _extract_single(self, data, path, default):
        parts = str(path).split('.') if path else []
        cur = data
        try:
            for part in parts:
                if isinstance(cur, list):
                    idx = int(part)
                    cur = cur[idx]
                elif isinstance(cur, dict):
                    cur = cur.get(part, default)
                else:
                    return default
            return cur
        except Exception:
            return default
