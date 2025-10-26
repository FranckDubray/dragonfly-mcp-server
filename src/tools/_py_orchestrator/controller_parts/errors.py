from pathlib import Path
from typing import Optional

class ValidationError(Exception):
    """Structured validation error with actionable guidance."""
    def __init__(self, message: str, *, code: str = "E000", file: Optional[str] = None, line: Optional[int] = None,
                 rule: Optional[str] = None, fix: Optional[str] = None, example: Optional[str] = None):
        super().__init__(message)
        self.code = code
        self.file = file
        self.line = line
        self.rule = rule
        self.fix = fix
        self.example = example


def make_error(message: str, *, code: str, file_path: Path, lineno: int, rule: str, fix: str, example: str) -> ValidationError:
    return ValidationError(
        message,
        code=code,
        file=str(file_path),
        line=int(lineno or 0),
        rule=rule,
        fix=fix,
        example=example,
    )
