import json
import re
from ..base import AbstractHandler, HandlerError

class NormalizeLlmOutputHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "normalize_llm_output"

    def _strip_fences(self, text: str) -> str:
        t = text.strip()
        if t.startswith("```"):
            lines = t.split("\n")
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            t = "\n".join(lines).strip()
        return t

    def _extract_first_json(self, text: str) -> str:
        start_idx = None
        for i, ch in enumerate(text):
            if ch in "[{":
                start_idx = i
                break
        if start_idx is None:
            raise HandlerError("No JSON object found in content", "INVALID_JSON", "validation", False)
        stack = []
        in_str = False
        esc = False
        for j in range(start_idx, len(text)):
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            else:
                if ch == '"':
                    in_str = True
                    continue
                if ch in "[{":
                    stack.append(ch)
                elif ch in "]}":
                    if not stack:
                        break
                    top = stack.pop()
                    if (top == "[" and ch != "]") or (top == "{" and ch != "}"):
                        raise HandlerError("Mismatched JSON brackets", "INVALID_JSON", "validation", False)
                    if not stack:
                        return text[start_idx:j+1]
        raise HandlerError("Unterminated JSON in content", "INVALID_JSON", "validation", False)

    def _repair_invalid_escapes(self, s: str) -> str:
        # Replace backslashes not followed by a valid escape with double backslash
        return re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', s)

    def run(self, content=None, **kwargs):
        try:
            if not content:
                raise HandlerError("Empty content", "EMPTY_INPUT", "validation", False)
            text = self._strip_fences(str(content))
            try:
                parsed = json.loads(text)
                return {"parsed": parsed}
            except json.JSONDecodeError:
                snippet = self._extract_first_json(text)
                try:
                    parsed = json.loads(snippet)
                    return {"parsed": parsed}
                except json.JSONDecodeError:
                    repaired = self._repair_invalid_escapes(snippet)
                    parsed = json.loads(repaired)
                    return {"parsed": parsed}
        except HandlerError:
            raise
        except json.JSONDecodeError as e:
            raise HandlerError(f"Invalid JSON: {str(e)[:200]}", "INVALID_JSON", "validation", False)
        except Exception as e:
            raise HandlerError(f"normalize_llm_output failed: {str(e)[:200]}", "PARSE_ERROR", "validation", False)
