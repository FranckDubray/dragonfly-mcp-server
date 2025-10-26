from ..base import AbstractHandler, HandlerError
import json
import re
from typing import Any, Dict, List, Optional

# Robust JSON normalizer for LLM outputs.
# Goals:
# - Accept fenced blocks (```json ... ``` or ``` ... ```), or raw text.
# - Extract the first complete JSON object/array when possible.
# - If content is truncated (unterminated), try to truncate to the last balanced bracket.
# - Repair common escape/control char issues inside strings.
# - Never raise on parse failure: return fallback_value (default: []).

class NormalizeLlmOutputHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "normalize_llm_output"

    # ---------- helpers ----------
    def _strip_fences_any(self, text: str) -> str:
        t = (text or "").strip()
        # Prefer ```json ... ``` fenced block
        m = re.search(r"```json\s*(.+?)\s*```", t, flags=re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1).strip()
        # Fallback: any ``` ... ```
        m = re.search(r"```\s*(.+?)\s*```", t, flags=re.DOTALL)
        if m:
            return m.group(1).strip()
        # No explicit fences → keep original
        return t

    def _first_complete_json_span(self, s: str) -> Optional[str]:
        # Return substring for the first complete {...} or [...] encountered.
        start = None
        stack: List[str] = []
        in_str = False
        esc = False
        last_balanced = None  # index after last fully balanced close
        for i, ch in enumerate(s):
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
                if ch in '[{':
                    if start is None:
                        start = i
                    stack.append(ch)
                elif ch in ']}':
                    if not stack:
                        continue
                    top = stack.pop()
                    if (top == '[' and ch != ']') or (top == '{' and ch != '}'):
                        return None
                    if not stack and start is not None:
                        last_balanced = i + 1
                        # we can return first complete JSON block found
                        return s[start:last_balanced]
        # If never fully balanced, try best-effort truncation to last closing brace/bracket
        if start is not None:
            j = max(s.rfind('}'), s.rfind(']'))
            if j >= start:
                return s[start:j+1]
        return None

    def _repair_invalid_escapes(self, s: str) -> str:
        # Replace lone backslashes not followed by a valid escape with double backslash
        return re.sub(r"\\(?![\\/\"bfnrtu])", r"\\\\", s)

    def _escape_ctrls_in_strings(self, s: str) -> str:
        # Encode raw control chars inside JSON strings
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

    # ---------- main ----------
    def run(self, content=None, fallback_value=None, **kwargs) -> Dict[str, Any]:
        try:
            # Pass-through: already structured
            if isinstance(content, (list, dict)):
                return {"parsed": content}
            if content is None:
                return {"parsed": fallback_value if fallback_value is not None else []}

            s = str(content)
            s = self._strip_fences_any(s)

            # Fast path: direct parse
            try:
                return {"parsed": json.loads(s)}
            except Exception:
                pass

            # Try extracting a complete span
            span = self._first_complete_json_span(s)
            if span:
                txt = self._escape_ctrls_in_strings(self._repair_invalid_escapes(span))
                try:
                    return {"parsed": json.loads(txt)}
                except Exception:
                    # Try one more time after trimming trailing commas
                    txt2 = re.sub(r",\s*([}\]])", r"\1", txt)
                    try:
                        return {"parsed": json.loads(txt2)}
                    except Exception:
                        pass

            # Fallback
            return {"parsed": fallback_value if fallback_value is not None else []}
        except Exception:
            # Never raise; always fallback
            return {"parsed": fallback_value if fallback_value is not None else []}

# TRANSFORM_META_START
{
  "io_type": "text->json",
  "description": "Robustly parse LLM outputs into JSON (handles fences, partial JSON, escapes; never raises)",
  "inputs": [
    "- content: string|object",
    "- fallback_value: any (optional; default: [])"
  ],
  "outputs": [
    "- parsed: any"
  ]
}
# TRANSFORM_META_END
