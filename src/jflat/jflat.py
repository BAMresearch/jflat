from typing import Any, Dict


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