# jflat

Utility functions to simplify/flatten **Pydantic JSON Schemas** into a compact, `$defs`-based format.

This project focuses on **schema transformation**, not flattening arbitrary JSON objects.

---

## What it does

Given a schema produced by **Pydantic v2** via `model_json_schema()`, `jflat` transforms it by:

- Ensuring the **root model** is placed inside `"$defs"`
- Removing noisy `"title"` keys everywhere
- Removing `"required"` lists and `"type": "object"` from definitions
- Adding an optional `"$inherits_from"` field (via an `inherits_map`)
- Optionally adding per-property `"mandatory": true/false` derived from `required`

---

## Installation (development)

Clone the repository and install in editable mode:

```bash
pip install -e .
````

***

## Usage

```python
from examples.schema import Method
from jflat import flatten_json_schema

schema = Method.model_json_schema()

flat = flatten_json_schema(
    schema,
    inherits_map={"Method": "BaseMethod"},
    add_mandatory=True,
)

# Result is always a dict with only "$defs" at top-level
print(flat.keys())              # dict_keys(["$defs"])
print(flat["$defs"].keys())     # includes "Method", "Person", ...
print(flat["$defs"]["Method"])  # transformed Method definition
```

### API

```python
flatten_json_schema(
    schema: dict,
    *,
    root_name: str | None = None,
    inherits_map: dict[str, str] | None = None,
    add_mandatory: bool = True,
) -> dict
```

*   `root_name`: Optional. If omitted, it is inferred from `schema["title"]` when available.
*   `inherits_map`: Optional. Mapping like `{"Child": "Base"}` to add `"$inherits_from": "#/$defs/Base"`.
*   `add_mandatory`: If `True`, adds `"mandatory": true/false` to each property.

***

## Examples

The folder `src/examples/` contains:

*   `schema.py`: Pydantic models used for demonstration and tests
*   `export_schema.py`: helper script to export `Method.model_json_schema()` to JSON for local inspection

> Exported JSON files are generated artifacts and are typically not committed to the repository.

***

## Testing

Run the test suite from the repository root:

```bash
pytest -q
```

***

## License

MIT (see `LICENSE`).

````

## After pasting (2 commands)
Run these from repo root:

```bash
pytest -q
git add README.md
git commit -m "Docs: update README for schema transformation"
git push
```


