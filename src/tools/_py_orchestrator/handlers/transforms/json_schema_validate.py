# TRANSFORM_META_START
{
  "io_type": "json->object",
  "description": "Validate JSON against a small JSON Schema subset (type, properties, required, additionalProperties, enum, minimum, maximum, items)",
  "inputs": [
    "- data: any",
    "- schema: object (subset JSON Schema)"
  ],
  "outputs": [
    "- ok: boolean",
    "- errors: list[object] (each: {path, keyword, message})"
  ]
}
# TRANSFORM_META_END

from typing import Any, Dict, List, Union

from ..base import AbstractHandler, HandlerError

MAX_ERRORS = 100


def _is_integer(x: Any) -> bool:
    # True pour ints Python, False pour floats décimaux
    return isinstance(x, int) and not isinstance(x, bool)


def _validate_type(data: Any, expected: str) -> bool:
    mapping = {
        "object": dict,
        "array": list,
        "string": str,
        "number": (int, float),
        "integer": int,  # on affinera avec _is_integer
        "boolean": bool,
        "null": type(None),
    }
    py_t = mapping.get(expected)
    if py_t is None:
        return True  # types inconnus => ignorer silencieusement
    if expected == "integer":
        return _is_integer(data)
    return isinstance(data, py_t)


def _add_error(errors: List[Dict[str, Any]], path: str, keyword: str, message: str):
    if len(errors) < MAX_ERRORS:
        errors.append({"path": path or "/", "keyword": keyword, "message": message})


def _join_path(parent: str, key: Union[str, int]) -> str:
    if parent == "" or parent == "/":
        return f"/{key}"
    return f"{parent}/{key}"


def _validate(data: Any, schema: Dict[str, Any], path: str, errors: List[Dict[str, Any]]):
    if len(errors) >= MAX_ERRORS:
        return

    # type
    s_type = schema.get("type")
    if s_type:
        if isinstance(s_type, list):
            if not any(_validate_type(data, t) for t in s_type):
                _add_error(errors, path, "type", f"expected one of {s_type}")
                return
        else:
            if not _validate_type(data, s_type):
                _add_error(errors, path, "type", f"expected {s_type}")
                return

    # enum
    if "enum" in schema:
        allowed = schema["enum"]
        ok = any(data == v for v in allowed)
        if not ok:
            _add_error(errors, path, "enum", f"value not in enum {allowed}")

    # numeric bounds
    if schema.get("type") in ("number", "integer"):
        if "minimum" in schema:
            try:
                if float(data) < float(schema["minimum"]):
                    _add_error(errors, path, "minimum", f"value < minimum {schema['minimum']}")
            except Exception:
                pass
        if "maximum" in schema:
            try:
                if float(data) > float(schema["maximum"]):
                    _add_error(errors, path, "maximum", f"value > maximum {schema['maximum']}")
            except Exception:
                pass

    # object
    if schema.get("type") == "object" and isinstance(data, dict):
        props = schema.get("properties", {})
        required = schema.get("required", [])
        additional = schema.get("additionalProperties", True)

        # required
        for req in required:
            if req not in data:
                _add_error(errors, _join_path(path, req), "required", "missing required property")

        # additionalProperties
        if additional is False:
            for k in data.keys():
                if k not in props:
                    _add_error(errors, _join_path(path, k), "additionalProperties", "unexpected property")

        # recurse known properties
        for k, subschema in props.items():
            if k in data:
                _validate(data[k], subschema or {}, _join_path(path, k), errors)

    # array
    if schema.get("type") == "array" and isinstance(data, list):
        items = schema.get("items")
        if items and isinstance(items, dict):
            for i, v in enumerate(data):
                _validate(v, items, _join_path(path, i), errors)


class JsonSchemaValidateHandler(AbstractHandler):
    @property
    def kind(self) -> str:
        return "json_schema_validate"

    def run(self, data=None, schema=None, **kwargs) -> Dict[str, Any]:
        """
        Args:
            data: any
            schema: dict (subset JSON Schema)
        Returns:
            { ok: bool, errors: [ {path, keyword, message} ] }
        """
        schema = schema or {}
        errors: List[Dict[str, Any]] = []
        try:
            _validate(data, schema, "", errors)
            return {"ok": len(errors) == 0, "errors": errors}
        except Exception as e:
            raise HandlerError(str(e), "JSON_SCHEMA_VALIDATE_ERROR", "validation", recoverable=False)
