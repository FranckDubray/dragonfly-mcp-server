import re, json
from ..base import AbstractHandler

class NormalizeLLMOutputHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "normalize_llm_output"

    def run(self, content, expected_format="json", fallback_value=None, **kwargs):
        if not isinstance(content, str):
            content = str(content)
        content = content.strip()
        if expected_format == "json":
            try:
                if content.startswith("```"):
                    m = re.search(r"```(?:json)?\s*\n(.*?)\n```", content, re.DOTALL)
                    if m:
                        content = m.group(1).strip()
                parsed = json.loads(content)
                return {"parsed": parsed, "success": True}
            except json.JSONDecodeError as e:
                return {"parsed": fallback_value, "success": False, "error": f"JSON parse error: {str(e)[:200]}"}
        elif expected_format == "lines":
            lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
            return {"parsed": lines, "success": True}
        else:
            return {"parsed": content, "success": True}
