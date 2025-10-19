# Domain-specific transforms: text processing, LLM output, data extraction

import re
import json
from .base import AbstractHandler, HandlerError

class SanitizeTextHandler(AbstractHandler):
    """
    Sanitize text: remove HTML, normalize whitespace, truncate.
    Useful for cleaning email bodies, web scraping, LLM inputs.
    """
    
    @property
    def kind(self) -> str:
        return "sanitize_text"
    
    def run(self, text, max_length=10000, remove_html=True, normalize_whitespace=True, **kwargs) -> dict:
        """
        Args:
            text: Input text (string)
            max_length: Max length (default: 10000)
            remove_html: Remove HTML tags (default: True)
            normalize_whitespace: Collapse multiple spaces/newlines (default: True)
        
        Returns:
            {
                "text": sanitized text,
                "truncated": bool,
                "original_length": int,
                "final_length": int
            }
        """
        if not isinstance(text, str):
            text = str(text)
        
        original_length = len(text)
        
        # Remove HTML tags
        if remove_html:
            text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace
        if normalize_whitespace:
            # Collapse multiple spaces
            text = re.sub(r' +', ' ', text)
            # Collapse multiple newlines
            text = re.sub(r'\n\n+', '\n\n', text)
        
        # Trim leading/trailing whitespace
        text = text.strip()
        
        # Truncate if needed
        truncated = len(text) > max_length
        if truncated:
            text = text[:max_length]
        
        return {
            "text": text,
            "truncated": truncated,
            "original_length": original_length,
            "final_length": len(text)
        }


class NormalizeLLMOutputHandler(AbstractHandler):
    """
    Normalize LLM output: extract JSON, parse fields, handle common issues.
    Useful for structured LLM responses (classification, extraction).
    """
    
    @property
    def kind(self) -> str:
        return "normalize_llm_output"
    
    def run(self, content, expected_format="json", fallback_value=None, **kwargs) -> dict:
        """
        Args:
            content: LLM response content (string)
            expected_format: "json" | "text" | "lines" (default: "json")
            fallback_value: Value to return if parsing fails (default: None)
        
        Returns:
            {
                "parsed": parsed value (dict/list/str),
                "success": bool,
                "error": str (if failed)
            }
        """
        if not isinstance(content, str):
            content = str(content)
        
        content = content.strip()
        
        if expected_format == "json":
            # Try to parse JSON
            try:
                # Remove markdown code blocks if present
                if content.startswith('```'):
                    # Extract content between ```json and ```
                    match = re.search(r'```(?:json)?\s*\n(.*?)\n```', content, re.DOTALL)
                    if match:
                        content = match.group(1).strip()
                
                parsed = json.loads(content)
                return {
                    "parsed": parsed,
                    "success": True
                }
            
            except json.JSONDecodeError as e:
                return {
                    "parsed": fallback_value,
                    "success": False,
                    "error": f"JSON parse error: {str(e)[:200]}"
                }
        
        elif expected_format == "lines":
            # Split by newlines, filter empty
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            return {
                "parsed": lines,
                "success": True
            }
        
        else:  # text
            return {
                "parsed": content,
                "success": True
            }


class JsonStringifyHandler(AbstractHandler):
    """
    Stringify Python object to JSON string.
    Useful for storing objects in SQLite TEXT fields, preparing payloads.
    """
    
    @property
    def kind(self) -> str:
        return "json_stringify"
    
    def run(self, value, ensure_ascii=False, indent=None, **kwargs) -> dict:
        """
        Args:
            value: Any Python object (dict, list, primitives)
            ensure_ascii: Escape non-ASCII (default: False, keeps UTF-8)
            indent: Pretty-print indent (default: None = compact)
        
        Returns:
            {
                "json_string": JSON string,
                "length": int (string length)
            }
        
        Example:
            value = {"name": "Alice", "items": [1, 2, 3]}
            → {"json_string": '{"name":"Alice","items":[1,2,3]}', "length": 34}
        """
        try:
            json_str = json.dumps(value, ensure_ascii=ensure_ascii, indent=indent)
            return {
                "json_string": json_str,
                "length": len(json_str)
            }
        except (TypeError, ValueError) as e:
            raise HandlerError(
                message=f"Cannot stringify to JSON: {str(e)[:200]}",
                code="JSON_STRINGIFY_ERROR",
                category="validation",
                retryable=False
            )


class ExtractFieldHandler(AbstractHandler):
    """
    Extract field(s) from nested object (JSONPath-like).
    
    Supports two modes:
    - Single field: path (string) → {"value": extracted}
    - Multiple fields: paths (dict) → {output1: val1, output2: val2, ...}
    
    Useful for transforming complex LLM/API responses.
    """
    
    @property
    def kind(self) -> str:
        return "extract_field"
    
    def run(self, data, path=None, paths=None, default=None, **kwargs) -> dict:
        """
        Args:
            data: Input object (dict/list)
            path: Single dotted path (e.g., "user.name") - for single extraction
            paths: Dict of {output_key: dotted_path} - for multi extraction
            default: Default value if path not found (default: None)
        
        Returns:
            Single mode: {"value": extracted value}
            Multi mode: {output_key1: val1, output_key2: val2, ...}
        
        Examples:
            # Single mode (backward compatible)
            data = {"score": 7.5, "feedback": "Good"}
            path = "score"
            → {"value": 7.5}
            
            # Multi mode (new)
            data = {"score": 7.5, "feedback": "Good"}
            paths = {"score": "score", "feedback": "feedback"}
            → {"score": 7.5, "feedback": "Good"}
        """
        if not isinstance(data, (dict, list)):
            if path:
                return {"value": default}
            elif paths:
                return {key: default for key in paths.keys()}
            return {"value": default}
        
        # Single field mode (backward compatible)
        if path:
            value = self._extract_single(data, path, default)
            return {"value": value}
        
        # Multi field mode (new)
        elif paths:
            result = {}
            for output_key, field_path in paths.items():
                result[output_key] = self._extract_single(data, field_path, default)
            return result
        
        # No path specified
        else:
            raise HandlerError(
                message="Either 'path' or 'paths' must be specified",
                code="EXTRACT_FIELD_MISSING_PATH",
                category="validation",
                retryable=False
            )
    
    def _extract_single(self, data, path, default):
        """Extract a single field from data using dotted path"""
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        
        return current


class FormatTemplateHandler(AbstractHandler):
    """
    Simple template formatting (string.format style).
    Useful for generating prompts, messages, reports.
    """
    
    @property
    def kind(self) -> str:
        return "format_template"
    
    def run(self, template, **kwargs) -> dict:
        """
        Args:
            template: Template string with {placeholders}
            **kwargs: Key-value pairs for substitution
        
        Returns:
            {"text": formatted string}
        
        Example:
            template = "Hello {name}, you have {count} messages"
            name = "Alice", count = 5
            → {"text": "Hello Alice, you have 5 messages"}
        """
        try:
            text = template.format(**kwargs)
            return {"text": text}
        except KeyError as e:
            raise HandlerError(
                message=f"Missing template variable: {e}",
                code="TEMPLATE_MISSING_VAR",
                category="validation",
                retryable=False
            )


class IdempotencyGuardHandler(AbstractHandler):
    """
    Check if action already done (idempotency guard).
    Useful for preventing duplicate operations (move email, send notification).
    """
    
    @property
    def kind(self) -> str:
        return "idempotency_guard"
    
    def run(self, action_id, completed_actions=None, **kwargs) -> dict:
        """
        Args:
            action_id: Unique action identifier (e.g., "move_email_12345")
            completed_actions: List of already completed action IDs (default: [])
        
        Returns:
            {
                "skip": bool (True if action already done),
                "action_id": str
            }
        """
        if completed_actions is None:
            completed_actions = []
        
        skip = action_id in completed_actions
        
        return {
            "skip": skip,
            "action_id": action_id
        }
