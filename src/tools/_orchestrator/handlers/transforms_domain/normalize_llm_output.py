import json
from ..base import AbstractHandler, HandlerError

class NormalizeLlmOutputHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "normalize_llm_output"

    def run(self, content=None, **kwargs):
        """Parse LLM JSON output (handle markdown fences, extract JSON)."""
        try:
            if not content:
                raise HandlerError("Empty content", "EMPTY_INPUT", "validation", False)
            
            text = str(content).strip()
            
            # Remove markdown code fences
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            
            # Parse JSON
            parsed = json.loads(text)
            return {"parsed": parsed}
            
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
