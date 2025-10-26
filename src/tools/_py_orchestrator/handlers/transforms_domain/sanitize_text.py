from ..base import AbstractHandler
import re

class SanitizeTextHandler(AbstractHandler):
    """
    Sanitize text: remove HTML, normalize whitespace, truncate.
    Useful for cleaning email bodies, web scraping, LLM inputs.
    """

    @property
    def kind(self) -> str:
        return "sanitize_text"

    def run(self, text, max_length=10000, remove_html=True, normalize_whitespace=True, **kwargs) -> dict:
        if not isinstance(text, str):
            text = str(text)

        original_length = len(text)

        if remove_html:
            text = re.sub(r'<[^>]+>', '', text)

        if normalize_whitespace:
            text = re.sub(r' +', ' ', text)
            text = re.sub(r'\n\n+', '\n\n', text)

        text = text.strip()

        truncated = len(text) > max_length
        if truncated:
            text = text[:max_length]

        return {
            "text": text,
            "truncated": truncated,
            "original_length": original_length,
            "final_length": len(text)
        }
# TRANSFORM_META_START
{
  "io_type": "text->text",
  "description": "Sanitize text (remove HTML, normalize whitespace, truncate)",
  "inputs": [
    "- text: string",
    "- max_length: integer (optional)",
    "- remove_html: boolean (optional)",
    "- normalize_whitespace: boolean (optional)"
  ],
  "outputs": [
    "- text: string",
    "- truncated: boolean",
    "- original_length: integer",
    "- final_length: integer"
  ]
}
# TRANSFORM_META_END
