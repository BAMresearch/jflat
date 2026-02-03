from __future__ import annotations

from jflat import flatten_json_schema
# import json

from jflat.jflat import flatten_json_schema
from examples.schema import Method  # works if tests run with pythonpath=src


def _contains_key_deep(obj, key: str) -> bool:
    if isinstance(obj, dict):
        if key in obj:
            return True
        return any(_contains_key_deep(v, key) for v in obj.values())
    if isinstance(obj, list):
        return any(_contains_key_deep(x, key) for x in obj)
    return False


def test_root_is_moved_into_defs():
    schema = Method.model_json_schema()
    out = flatten_json_schema(schema, inherits_map={"Method": "BaseMethod"})

    assert "$defs" in out
    assert "Method" in out["$defs"]
    assert "properties" in out["$defs"]["Method"]


def test_titles_and_required_are_removed():
    schema = Method.model_json_schema()
    out = flatten_json_schema(schema, inherits_map={"Method": "BaseMethod"})

    assert not _contains_key_deep(out, "title")
    assert not _contains_key_deep(out, "required")


def test_type_object_is_removed_from_definitions():
    schema = Method.model_json_schema()
    out = flatten_json_schema(schema, inherits_map={"Method": "BaseMethod"})

    for name, definition in out["$defs"].items():
        if isinstance(definition, dict):
            assert definition.get("type") != "object"


def test_inheritance_is_added():
    schema = Method.model_json_schema()
    out = flatten_json_schema(schema, inherits_map={"Method": "BaseMethod"})

    assert out["$defs"]["Method"]["$inherits_from"] == "#/$defs/BaseMethod"


def test_mandatory_flags_are_added_correctly():
    schema = Method.model_json_schema()
    out = flatten_json_schema(schema, inherits_map={"Method": "BaseMethod"}, add_mandatory=True)

    props = out["$defs"]["Method"]["properties"]

    # required in Method: author (inherited field still appears in schema), method_name, person
    assert props["method_name"]["mandatory"] is True
    assert props["person"]["mandatory"] is True

    # optional field
    assert props["comment"]["mandatory"] is False

