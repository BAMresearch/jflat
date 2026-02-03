def test_public_api_import_smoke():
    # If this test passes, it means the package init (__init__.py) is healthy
    # and does not have circular imports.
    assert callable(flatten_json_schema)


def test_does_not_mutate_input_schema():
    schema = Method.model_json_schema()
    original = copy.deepcopy(schema)

    _ = flatten_json_schema(schema, inherits_map={"Method": "BaseMethod"})

    assert schema == original, "flatten_json_schema must not modify the input dict in-place"


def test_add_mandatory_false_removes_mandatory_keys():
    schema = Method.model_json_schema()
    out = flatten_json_schema(
        schema,
        inherits_map={"Method": "BaseMethod"},
        add_mandatory=False,
    )

    method_props = out["$defs"]["Method"]["properties"]

    # No property should contain "mandatory" if add_mandatory=False
    assert all(
        not (isinstance(prop_schema, dict) and "mandatory" in prop_schema)
        for prop_schema in method_props.values()
    )


def test_root_name_is_inferred_from_title():
    schema = Method.model_json_schema()

    # Do not pass root_name; it should be inferred from schema["title"]
    out = flatten_json_schema(schema, inherits_map={"Method": "BaseMethod"})

    assert "$defs" in out
    assert "Method" in out["$defs"], "Root model should be placed into $defs using inferred root name"


def test_output_has_only_defs_top_level():
    schema = Method.model_json_schema()
    out = flatten_json_schema(schema, inherits_map={"Method": "BaseMethod"})

    # Very strict: only $defs at top-level
    assert set(out.keys()) == {"$defs"}
    