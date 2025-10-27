# TRANSFORM_META_START
{
  "io_type": "text->json",
  "description": "Robustly extract JSON (array/object) from LLM output with optional prose/code fences before/after; tolerant repairs",
  "inputs": [
    "- content: string|json",
    "- fallback_value: any (optional)"
  ],
  "outputs": [
    "- parsed: any"
  ]
}
# TRANSFORM_META_END

from ..base import AbstractHandler, HandlerError
import json
import re
from typing import Any, Tuple

class NormalizeLlmOutputHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "normalize_llm_output"

    def run(self, content=None, fallback_value=None, **kwargs):
        try:
            # Already structured
            if isinstance(content, (list, dict)):
                return {"parsed": content}
            if content is None:
                return {"parsed": fallback_value if fallback_value is not None else []}
            text = str(content)
            # Strip common code fences ```json ... ``` or ``` ... ```
            text = self._strip_fences(text)
            # Try direct JSON first
            obj, ok = self._try_load(text)
            if ok:
                return {"parsed": obj}
            # Extract first balanced JSON value (object/array) from text (with string awareness)
            frag = self._extract_first_json(text)
            if frag:
                # Repair common issues then parse
                frag = self._repair_invalid_escapes(frag)
                frag = self._escape_ctrls_in_strings(frag)
                obj, ok = self._try_load(frag)
                if ok:
                    return {"parsed": obj}
            # As a last resort: look for last balanced JSON (sometimes tail is valid)
            frag2 = self._extract_last_json(text)
            if frag2:
                frag2 = self._repair_invalid_escapes(frag2)
                frag2 = self._escape_ctrls_in_strings(frag2)
                obj, ok = self._try_load(frag2)
                if ok:
                    return {"parsed": obj}
            # Fallback
            return {"parsed": fallback_value if fallback_value is not None else []}
        except Exception as e:
            raise HandlerError(f"normalize_llm_output failed: {str(e)[:200]}", "NORMALIZE_LLM_OUTPUT_ERROR", "validation", False)

    # ---- Helpers ---------------------------------------------------------

    def _strip_fences(self, s: str) -> str:
        t = s.strip()
        if t.startswith("```"):
            # remove first fence line
            lines = t.splitlines()
            if lines:
                lines = lines[1:]
            # strip trailing fence
            while lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            return "\n".join(lines).strip()
        return t

    def _try_load(self, s: str) -> Tuple[Any, bool]:
        try:
            return json.loads(s), True
        except Exception:
            return None, False

    def _repair_invalid_escapes(self, s: str) -> str:
        # Replace backslashes not forming a valid escape with double backslash
        return re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', s)

    def _escape_ctrls_in_strings(self, s: str) -> str:
        # Walk and escape raw control chars only inside quoted strings
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
                        out.append(ch); esc = True
                    elif ch == '"':
                        out.append(ch); in_str = False
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

    def _extract_first_json(self, text: str) -> str | None:
        # Find first '{' or '[' then balance braces/brackets with string awareness
        start = None
        for i, ch in enumerate(text):
            if ch == '{' or ch == '[':
                start = i; break
        if start is None:
            return None
        return self._scan_balanced(text, start)

    def _extract_last_json(self, text: str) -> str | None:
        # From the end, locate last '{' or '[' and try scan; helps when trailing section is valid
        for i in range(len(text) - 1, -1, -1):
            if text[i] in '{[':
                frag = self._scan_balanced(text, i)
                if frag:
                    return frag
        return None

    def _scan_balanced(self, text: str, start: int) -> str | None:
        stack = []
        in_str = False
        esc = False
        for j in range(start, len(text)):
            ch = text[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            else:
                if ch == '"':
                    in_str = True
                    continue
                if ch in '{[':
                    stack.append(ch)
                elif ch in '}]':
                    if not stack:
                        return None
                    top = stack.pop()
                    if (top == '{' and ch != '}') or (top == '[' and ch != ']'):
                        return None
                    if not stack:
                        return text[start:j+1]
        return None

# End

# TRANSFORM_META_START
{
  "io_type": "text->json",
  "description": "Robustly extract JSON (array/object) from LLM output with optional prose/code fences before/after; tolerant repairs",
  "inputs": [
    "- content: string|json",
    "- fallback_value: any (optional)"
  ],
  "outputs": [
    "- parsed: any"
  ]
}
# TRANSFORM_META_END
