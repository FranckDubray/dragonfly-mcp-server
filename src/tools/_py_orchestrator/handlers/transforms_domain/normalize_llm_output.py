















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
            # strip trailing code fence if present
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            t = "\n".join(lines).strip()
        return t

    def _extract_first_json(self, text: str) -> str:
        # Robust extraction: find first '{' or '[' and then walk to matching '}' or ']'
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
        return re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', s)

    def _escape_control_chars_in_strings(self, s: str) -> str:
        """Escape raw control characters (\n, \r, \t, etc.) only when inside JSON strings."""
        out = []
        in_str = False
        esc = False
        for ch in s:
            if in_str:
                if esc:
                    out.append(ch)
                    esc = False
                else:
                    if ch == '\\':
                        out.append(ch)
                        esc = True
                    elif ch == '"':
                        out.append(ch)
                        in_str = False
                    elif ch == '\n':
                        out.append('\\n')
                    elif ch == '\r':
                        out.append('\\r')
                    elif ch == '\t':
                        out.append('\\t')
                    elif ord(ch) < 32:
                        out.append(f"\\u{ord(ch):04x}")
                    else:
                        out.append(ch)
            else:
                out.append(ch)
                if ch == '"':
                    in_str = True
        return ''.join(out)

    def _extract_from_fenced_block(self, text: str) -> str | None:
        """
        Try to extract JSON from a ```json ... ``` fenced block anywhere in the text.
        Returns the inner content if found, else None.
        """
        # Look for ```json ... ``` ... ``` patterns lazily
        m = re.search(r"```json\s*(.+?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if not m:
            return None
        inner = m.group(1).strip()
        return inner

    def run(self, content=None, fallback_value=None, **kwargs):
        try:
            # Pass-through if already parsed
            if isinstance(content, (dict, list)):
                return {"parsed": content}
            if not content:
                if fallback_value is not None:
                    return {"parsed": fallback_value}
                raise HandlerError("Empty content", "EMPTY_INPUT", "validation", False)

            raw = str(content)

            # 1) Direct JSON if possible
            try:
                return {"parsed": json.loads(raw)}
            except json.JSONDecodeError:
                pass

            # 2) If a fenced ```json block exists anywhere, parse inside it
            fenced = self._extract_from_fenced_block(raw)
            if fenced:
                try:
                    return {"parsed": json.loads(fenced)}
                except json.JSONDecodeError:
                    # Try repairs on fenced content
                    repaired = self._repair_invalid_escapes(fenced)
                    try:
                        return {"parsed": json.loads(repaired)}
                    except json.JSONDecodeError:
                        repaired2 = self._escape_control_chars_in_strings(repaired)
                        return {"parsed": json.loads(repaired2)}

            # 3) Extract the first JSON object/array from anywhere in the text
            snippet = self._extract_first_json(raw)
            try:
                return {"parsed": json.loads(snippet)}
            except json.JSONDecodeError:
                repaired = self._repair_invalid_escapes(snippet)
                try:
                    return {"parsed": json.loads(repaired)}
                except json.JSONDecodeError:
                    repaired2 = self._escape_control_chars_in_strings(repaired)
                    return {"parsed": json.loads(repaired2)}

        except HandlerError:
            raise
        except json.JSONDecodeError as e:
            raise HandlerError(f"Invalid JSON: {str(e)[:200]}", "INVALID_JSON", "validation", False)
        except Exception as e:
            raise HandlerError(f"normalize_llm_output failed: {str(e)[:200]}", "PARSE_ERROR", "validation", False)

# TRANSFORM_META_START
{
  "io_type": "text/json->json",
  "description": "Parse tolerant LLM text/JSON into structured JSON (normalize output)",
  "inputs": [
    "- content: string|json",
    "- fallback_value: any (optional)"
  ],
  "outputs": [
    "- parsed: any"
  ]
}
# TRANSFORM_META_END
