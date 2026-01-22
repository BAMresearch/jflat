# examples/demo.py
# Minimal demo that loads a sample JSON, flattens it, and prints the result.

import json
from pathlib import Path
from jflat.models.io import FlattenOptions, FlattenRequest
from jflat.core.flattener import flatten

INPUT = Path(__file__).parent / "sample.json"

with INPUT.open("r", encoding="utf-8") as f:
    raw = json.load(f)

# Build request with default options: "_" separator, preserve lists
req = FlattenRequest(
    data=raw,
    options=FlattenOptions(sep="_", preserve_lists=True),
)

# Perform flattening and print
resp = flatten(req)
print("Mode:", resp.mode)
print(json.dumps(resp.result.data, ensure_ascii=False, indent=2))