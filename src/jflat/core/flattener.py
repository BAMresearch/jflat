# jflat/core/flattener.py
# Core flattening logic.
# The public APIs accept/return Pydantic models (FlattenRequest/FlattenResponse),
# which improves clarity, validation, and maintainability.

from __future__ import annotations
from typing import Any
from jflat.models.io import FlattenOptions, FlattenRequest, FlattenedDict, FlattenResponse


def _flatten(
    data: Any,
    *,
    parent_key: str = "",
    options: FlattenOptions,
    depth: int = 0,
) -> dict[str, Any]:
    """
    Internal recursive function that flattens 'data' into a simple dict.

    Behavior:
      - dict: traverse its keys and accumulate flattened entries
      - list: either preserve as list (preserve_lists=True) or index its items into keys
      - primitive (str/int/float/bool/None): stored under the current parent key
      - max_depth: if set and reached, stop descending and store the nested structure as-is

    Args:
      data:        any JSON-like structure (dict, list, primitive)
      parent_key:  current flattened key prefix
      options:     FlattenOptions (separator, depth, list handling)
      depth:       current recursion depth

    Returns:
      A flat dict with composite keys joined by 'options.sep'.
    """
    flat: dict[str, Any] = {}
    sep = options.sep

    # If we hit the depth limit, stop recursion and store the value as-is.
    if options.max_depth is not None and depth >= options.max_depth:
        if parent_key:
            flat[parent_key] = data
        else:
            # Root-level with depth exceeded is rare; still keep content visible.
            if isinstance(data, dict):
                for k, v in data.items():
                    flat[k] = v
            else:
                flat["value"] = data
        return flat

    # Handle dicts: recurse into each key/value
    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            flat.update(_flatten(v, parent_key=new_key, options=options, depth=depth + 1))
        return flat

    # Handle lists: either keep the list or index into new keys
    if isinstance(data, list):
        if options.preserve_lists:
            # Keep the entire list under the current key
            if parent_key:
                flat[parent_key] = data
            else:
                flat["list"] = data
            return flat
        else:
            # Flatten list items using numeric indices
            for idx, item in enumerate(data):
                new_key = f"{parent_key}{sep}{idx}" if parent_key else str(idx)
                flat.update(_flatten(item, parent_key=new_key, options=options, depth=depth + 1))
            return flat

    # Handle primitives: store the value under the current key
    if parent_key:
        flat[parent_key] = data
    else:
        flat["value"] = data
    return flat


def flatten_to_dict(req: FlattenRequest) -> FlattenedDict:
    """
    Public API: flatten a nested JSON object to a flat dict according to options.

    Args:
      req: FlattenRequest Pydantic model (data + options)

    Returns:
      FlattenedDict: Pydantic model containing the flat map
    """
    flat = _flatten(req.data, parent_key="", options=req.options, depth=0)
    return FlattenedDict(data=flat)


def flatten(req: FlattenRequest) -> FlattenResponse:
    """
    Higher-level API returning a formal response wrapper (future-friendly).
    For now, only 'dict' mode is supported.

    Args:
      req: FlattenRequest

    Returns:
      FlattenResponse with 'mode' and 'result'
    """
    result = flatten_to_dict(req)
    return FlattenResponse(mode="dict", result=result)