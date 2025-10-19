import re
from ..base import AbstractHandler

class SanitizeTextHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "sanitize_text"

    def run(self, text, max_length=10000, remove_html=True, normalize_whitespace=True, **kwargs):
        if not isinstance(text, str):
            text = str(text)
        original_length = len(text)
        if remove_html:
            text = re.sub(r"<[^>]+>", "", text)
        if normalize_whitespace:
            text = re.sub(r" +", " ", text)
            text = re.sub(r"\n\n+", "\n\n", text)
        text = text.strip()
        truncated = len(text) > max_length
        if truncated:
            text = text[:max_length]
        return {"text": text, "truncated": truncated, "original_length": original_length, "final_length": len(text)}
