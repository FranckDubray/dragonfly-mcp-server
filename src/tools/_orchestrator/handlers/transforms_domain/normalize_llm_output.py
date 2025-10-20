import json
from ..base import AbstractHandler, HandlerError

class NormalizeLlmOutputHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "normalize_llm_output"

    def _strip_fences(self, text: str) -> str:
        t = text.strip()
        if t.startswith("```"):
            lines = t.split("\n")
            # drop first fence line
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            # drop trailing fence line
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            t = "\n".join(lines).strip()
        return t

    def _extract_first_json(self, text: str) -> str:
        # Attempt to find the first balanced JSON object/array
        start_idx = None
        for i, ch in enumerate(text):
            if ch in "[{":
                start_idx = i
                break
        if start_idx is None:
            raise HandlerError(
                message="No JSON object found in content",
                code="INVALID_JSON",
                category="validation",
                retryable=False
            )
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
                        raise HandlerError(
                            message="Mismatched JSON brackets",
                            code="INVALID_JSON",
                            category="validation",
                            retryable=False
                        )
                    if not stack:
                        # closed top-level
                        snippet = text[start_idx:j+1]
                        return snippet
        raise HandlerError(
            message="Unterminated JSON in content",
            code="INVALID_JSON",
            category="validation",
            retryable=False
        )

    def run(self, content=None, **kwargs):
        """Parse LLM JSON output robustly (remove fences, extract first JSON block)."""
        try:
            if not content:
                raise HandlerError("Empty content", "EMPTY_INPUT", "validation", False)
            text = self._strip_fences(str(content))
            try:
                # quick path
                parsed = json.loads(text)
                return {"parsed": parsed}
            except json.JSONDecodeError:
                # extract first JSON block and parse
                snippet = self._extract_first_json(text)
                parsed = json.loads(snippet)
                return {"parsed": parsed}
        except HandlerError:
            raise
        except json.JSONDecodeError as e:
            raise HandlerError(
                message=f"Invalid JSON: {str(e)[:200]}",
                code="INVALID_JSON",
                category="validation",
                retryable=False
            )
        except Exception as e:
            raise HandlerError(
                message=f"normalize_llm_output failed: {str(e)[:200]}",
                code="PARSE_ERROR",
                category="validation",
                retryable=False
            )
