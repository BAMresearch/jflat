from typing import Any, Dict, Optional





def flatten_json_schema(
    schema: dict[str, Any],
    *,
    root_name: Optional[str] = None,
    inherits_map: Optional[dict[str, str]] = None,
    add_mandatory: bool = True,
) -> dict[str, Any]:
    """
    Convert a Pydantic JSON Schema (model_json_schema()) into a simplified schema
    format used by this project.

    Transformations:
    - Ensure everything is inside "$defs" (including the root model)
    - Remove "title" everywhere
    - Remove "required" and "type": "object" from model definitions
    - Add "$inherits_from" using inherits_map
    - Optionally add "mandatory": true/false per property (derived from "required")
    """
    inherits_map = inherits_map or {}

    # --- helpers -------------------------------------------------------------

    def remove_keys_deep(obj: Any, keys_to_remove: set[str]) -> Any:
        if isinstance(obj, dict):
            return {
                k: remove_keys_deep(v, keys_to_remove)
                for k, v in obj.items()
                if k not in keys_to_remove
            }
        if isinstance(obj, list):
            return [remove_keys_deep(x, keys_to_remove) for x in obj]
        return obj

    def transform_definition(def_obj: dict[str, Any], def_name: str) -> dict[str, Any]:
        required_list = def_obj.get("required", [])
        required = set(required_list) if isinstance(required_list, list) else set()

        cleaned = dict(def_obj)

        # remove object-level noise
        cleaned.pop("title", None)
        cleaned.pop("required", None)
        if cleaned.get("type") == "object":
            cleaned.pop("type", None)

        # properties cleanup + mandatory
        props = cleaned.get("properties")
        if isinstance(props, dict):
            new_props: dict[str, Any] = {}
            for prop_name, prop_schema in props.items():
                if isinstance(prop_schema, dict):
                    pc = dict(prop_schema)
                    pc.pop("title", None)
                    if add_mandatory:
                        pc["mandatory"] = prop_name in required
                    new_props[prop_name] = pc
                else:
                    new_props[prop_name] = prop_schema
            cleaned["properties"] = new_props

        # inheritance
        base = inherits_map.get(def_name)
        if base:
            cleaned["$inherits_from"] = f"#/$defs/{base}"

        return cleaned

    # --- main ----------------------------------------------------------------

    # Start from existing $defs
    defs: dict[str, Any] = {}
    if isinstance(schema.get("$defs"), dict):
        defs.update(schema["$defs"])

    # Infer root name if not provided (Pydantic usually puts the model name in "title")
    if root_name is None:
        root_name = schema.get("title")

    # If root schema has content outside $defs, move it into $defs[root_name]
    root_payload = {k: v for k, v in schema.items() if k not in {"$defs", "$schema"}}
    if root_name and root_payload:
        # Only set if not already present; otherwise prefer existing $defs entry
        defs.setdefault(root_name, root_payload)

    # Transform each definition
    transformed: dict[str, Any] = {}
    for def_name, def_obj in defs.items():
        if isinstance(def_obj, dict):
            transformed[def_name] = transform_definition(def_obj, def_name)
        else:
            transformed[def_name] = def_obj

    # Final deep cleanup (titles are pure noise for this project)
    result = {"$defs": transformed}
    result = remove_keys_deep(result, {"title"})

    return result





