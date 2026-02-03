# jflat

Utility functions to simplify/flatten **Pydantic JSON Schemas** into a compact, `$defs`-based format.

This project focuses on **schema transformation**, not flattening arbitrary JSON objects.

## What it does

Given a schema produced by `Pydantic v2` via `model_json_schema()`, `jflat` transforms it by:

- Ensuring the **root model** is placed inside `"$defs"`
- Removing noisy `"title"` keys everywhere
- Removing `"required"` lists and `"type": "object"` from definitions
- Adding an optional `"$inherits_from"` field (via an `inherits_map`)
- Optionally adding per-property `"mandatory": true/false` derived from `required`

## Installation (development)

Clone the repository and install in editable mode:

```bash
pip install -e .
