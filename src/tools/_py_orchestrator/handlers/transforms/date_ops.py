# TRANSFORM_META_START
{
  "io_type": "json->json",
  "description": "Date utilities: parametric operations (format/add/diff)",
  "inputs": [
    "- ops: list[object] (each op: {op, value|a|b, to|unit, days|hours|minutes|seconds, save_as})"
  ],
  "outputs": [
    "- object: object (keys produced via save_as)"
  ]
}
# TRANSFORM_META_END

