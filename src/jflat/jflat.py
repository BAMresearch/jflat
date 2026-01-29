from typing import Any, Dict
from pydantic import BaseModel, Field


class JFlat:
    """
    A tiny helper class that accepts a nested JSON-like dictionary
    and flattens it into a single-level dictionary.

    Example:
        {"person": {"name": "Alice"}}
        becomes:
        {"person_name": "Alice"}
    """

    def __init__(self, input_json: Dict[str, Any]):
        if not isinstance(input_json, dict):
            raise ValueError("JFlat only accepts dictionaries.")
        self.input_json = input_json

    def flatten(self) -> Dict[str, Any]:
        flat_dict: Dict[str, Any] = {}
        self._flatten_recursive(self.input_json, parent_key="", output=flat_dict)
        return flat_dict

    def _flatten_recursive(self, obj: Any, parent_key: str, output: Dict[str, Any]):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{parent_key}_{key}" if parent_key else key
                self._flatten_recursive(value, new_key, output)
        else:
            output[parent_key] = obj


# ================================================================
#  PART 3 — DEMO EXECUTION
# ================================================================
if __name__ == "__main__":
    print("\n=== Pydantic -> JSON SCHEMA ===")
    schema = Method.model_json_schema()
    print(schema)

    print("\n=== Nested JSON produced by Pydantic ===")
    method_instance = Method(
        author="Maxim",
        method_name="FlattenSchema",
        person=Person(
            name="Christopher Nolan",
            age=50,
            example=Example(id="XYZ123")
        )
    )

    nested_json = method_instance.model_dump()
    print(nested_json)

    print("\n=== Flattened using JFlat ===")
    flat = JFlat(nested_json).flatten()
    print(flat)








