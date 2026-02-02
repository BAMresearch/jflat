from typing import Any, Dict, Optional


def flatten_json(data: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
    """
    Flatten a nested JSON-like dictionary into a flat dictionary
    using underscore-separated keys.

    Example:
        {"person": {"name": "Alice"}}
    becomes:
        {"person_name": "Alice"}
    """
    result: Dict[str, Any] = {}

    for key, value in data.items():
        new_key = f"{parent_key}_{key}" if parent_key else key

        if isinstance(value, dict):
            # Recursively flatten child dictionaries
            result.update(flatten_json(value, new_key))
        else:
            result[new_key] = value

    return result


def flatten_json_schema(
    schema: Dict[str, Any],
    *,
    root_name: Optional[str] = None,
    inherits_map: Optional[Dict[str, str]] = None,
    add_mandatory: bool = True,
) -> Dict[str, Any]:
    """
    Convert a Pydantic JSON Schema (model_json_schema()) into a simplified
    flattened schema format used by this project.

    Main transformations:
    - Move root model into $defs (if needed)
    - Remove 'title' keys (object + property titles)
    - Remove 'required' and 'type': 'object'
    - Add '$inherits_from' using inherits_map
    - Optionally add 'mandatory': true/false per property
    """
    inherits_map = inherits_map or {}
    result: Dict[str, Any] = {"$defs": {}}

    # 1) Copy $defs (if present)
    defs = schema.get("$defs", {})
    if isinstance(defs, dict):
        result["$defs"].update(defs)

    # 2) Move root model into $defs if it exists at top-level
    # Pydantic often returns root properties at top-level, not under $defs.
    if root_name:
        root_def = {k: v for k, v in schema.items() if k not in {"$defs", "$schema"}}
        if root_def:
            result["$defs"][root_name] = root_def

    # Helper: remove keys recursively
    def _remove_keys(obj: Any, keys_to_remove: set[str]) -> Any:
        if isinstance(obj, dict):
            return {
                k: _remove_keys(v, keys_to_remove)
                for k, v in obj.items()
                if k not in keys_to_remove
            }
        if isinstance(obj, list):
            return [_remove_keys(x, keys_to_remove) for x in obj]
        return obj

    # Helper: transform one definition object
    def _transform_def(def_obj: Dict[str, Any], def_name: str) -> Dict[str, Any]:
        required = set(def_obj.get("required", [])) if isinstance(def_obj.get("required"), list) else set()

        # Remove object-level noise
        cleaned = dict(def_obj)
        cleaned.pop("title", None)
        cleaned.pop("required", None)
        if cleaned.get("type") == "object":
            cleaned.pop("type", None)

        # Properties cleanup + optional 'mandatory'
        props = cleaned.get("properties")
        if isinstance(props, dict):
            new_props: Dict[str, Any] = {}
            for prop_name, prop_schema in props.items():
                if isinstance(prop_schema, dict):
                    prop_clean = dict(prop_schema)
                    prop_clean.pop("title", None)

                    if add_mandatory:
                        prop_clean["mandatory"] = prop_name in required

                    new_props[prop_name] = prop_clean
                else:
                    new_props[prop_name] = prop_schema
            cleaned["properties"] = new_props

        # Add inheritance info if known
        if def_name in inherits_map:
            base = inherits_map[def_name]
            cleaned["$inherits_from"] = f"#/$defs/{base}"

        return cleaned

    # 3) Transform each $defs entry
    transformed_defs: Dict[str, Any] = {}
    for def_name, def_obj in result["$defs"].items():
        if isinstance(def_obj, dict):
            transformed_defs[def_name] = _transform_def(def_obj, def_name)
        else:
            transformed_defs[def_name] = def_obj

    result["$defs"] = transformed_defs

    # 4) Extra cleanup: remove any remaining titles deeply (safe)
    result = _remove_keys(result, {"title"})

    return result