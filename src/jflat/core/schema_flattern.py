
# jflat/core/schema_flattener.py
"""
Flatten a Pydantic v2 JSON Schema into a dict that:
- keeps $defs as top-level
- for each model in $defs:
  - includes only fields that are NOT $ref (i.e. not other BaseModels)
  - collects referenced BaseModels into $contains
  - collects inheritance info into $inherits_from (from allOf)
"""

from __future__ import annotations
from typing import Any, Optional

import json

try:
    # We only import pydantic types optionally,
    # so this class can still accept a dict without importing pydantic everywhere.
    from pydantic import BaseModel
except Exception:  # pragma: no cover
    BaseModel = object  # type: ignore

from jflat.core.schema_base import AbstractSchemaFlattener


_JSON_TYPE_TO_PYTHON = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "object": dict,
    "array": list,
}


def _schema_type_to_python(field_schema: dict[str, Any]) -> Any:
    """
    Convert JSON Schema 'type' or 'anyOf' into a Python type object.

    This is intentionally simple for a prototype:
    - Handles {"type": "string"} -> str
    - Handles {"type": ["string", "null"]} -> str (optional)
    - Handles {"anyOf": [{"type":"string"}, {"type":"null"}]} -> str (optional)
    Otherwise returns object as fallback.
    """
    # anyOf often appears for Optional fields
    if "anyOf" in field_schema and isinstance(field_schema["anyOf"], list):
        candidates = field_schema["anyOf"]
        non_null = [c for c in candidates if c.get("type") != "null"]
        if non_null:
            return _schema_type_to_python(non_null[0])
        return object

    t = field_schema.get("type")

    # type can be a list (e.g., ["string", "null"])
    if isinstance(t, list):
        t_no_null = [x for x in t if x != "null"]
        if len(t_no_null) == 1:
            return _JSON_TYPE_TO_PYTHON.get(t_no_null[0], object)
        return object

    if isinstance(t, str):
        return _JSON_TYPE_TO_PYTHON.get(t, object)

    return object


class PydanticSchemaFlattener(AbstractSchemaFlattener):
    """
    Accepts either:
    - a dict representing a Pydantic JSON schema
    - a Pydantic BaseModel class (recommended)
    - a Pydantic BaseModel instance (also OK)
    """

    def _validate_and_build_schema(self, schema_or_source: Any) -> dict[str, Any]:
        # Case 1: already a dict (schema)
        if isinstance(schema_or_source, dict):
            if "$defs" not in schema_or_source:
                raise ValueError("Input dict does not look like a Pydantic JSON Schema (missing '$defs').")
            return schema_or_source

        # Case 2: a Pydantic model class
        if isinstance(schema_or_source, type) and hasattr(schema_or_source, "model_json_schema"):
            schema = schema_or_source.model_json_schema()
            if "$defs" not in schema:
                raise ValueError("Generated schema has no '$defs'. Did you pass the correct model?")
            return schema

        # Case 3: a Pydantic model instance
        if hasattr(schema_or_source, "__class__") and hasattr(schema_or_source.__class__, "model_json_schema"):
            schema = schema_or_source.__class__.model_json_schema()
            if "$defs" not in schema:
                raise ValueError("Generated schema has no '$defs'. Did you pass the correct model instance?")
            return schema

        raise TypeError("Unsupported input. Provide a schema dict or a Pydantic BaseModel class/instance.")

    def flatten(self) -> dict[str, Any]:
        schema = self._schema
        defs: dict[str, Any] = schema.get("$defs", {})

        out: dict[str, Any] = {"$defs": {}}

        for def_name, def_schema in defs.items():
            model_entry: dict[str, Any] = {}

            # 1) Detect inheritance via "allOf"
            local_schema = def_schema
            inherits_from: Optional[str] = None

            if "allOf" in def_schema and isinstance(def_schema["allOf"], list):
                # allOf usually contains:
                # - one $ref to base model
                # - one object schema containing "properties"
                for part in def_schema["allOf"]:
                    if isinstance(part, dict) and "$ref" in part:
                        inherits_from = part["$ref"]
                    if isinstance(part, dict) and ("properties" in part or part.get("type") == "object"):
                        local_schema = part  # use the part that contains properties

            if inherits_from:
                model_entry["$inherits_from"] = inherits_from

            # 2) Extract properties (fields)
            props: dict[str, Any] = local_schema.get("properties", {}) if isinstance(local_schema, dict) else {}
            contains: list[str] = []

            for field_name, field_schema in props.items():
                # If field is a reference to another model => treat as "contains"
                if isinstance(field_schema, dict) and "$ref" in field_schema:
                    ref = field_schema["$ref"]
                    contains.append(f"{field_name}{ref}")  # matches your example: field#/$defs/Other
                    continue

                # Otherwise: keep this as a "normal field"
                python_type = _schema_type_to_python(field_schema if isinstance(field_schema, dict) else {})
                desc = field_schema.get("description") if isinstance(field_schema, dict) else None

                field_info: dict[str, Any] = {"type": python_type}
                if desc:
                    field_info["description"] = desc

                model_entry[field_name] = field_info

            # 3) Save contains list (even if empty for consistency)
            model_entry["$contains"] = contains

            out["$defs"][def_name] = model_entry

        return out

    def to_json(self, *, indent: int = 2) -> str:
        """
        JSON output cannot contain Python type objects directly.
        We convert types like <class 'str'> into the string "str".
        """

        def default_encoder(obj: Any) -> Any:
            if isinstance(obj, type):
                return obj.__name__  # str -> "str", int -> "int"
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.dumps(self.flatten(), indent=indent, ensure_ascii=False, default=default_encoder)

