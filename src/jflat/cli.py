# jflat/cli.py
# A tiny CLI for demos: read JSON, flatten it, print or write to a file.

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from jflat.models.io import FlattenOptions, FlattenRequest
from jflat.core.flattener import flatten_to_dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Flatten a nested JSON file.")
    parser.add_argument("input", type=Path, help="Path to input JSON file")
    parser.add_argument("-o", "--output", type=Path, help="Path to write flattened JSON")
    parser.add_argument("--sep", default="_", help="Key separator (default: _)")
    parser.add_argument("--max-depth", type=int, default=None, help="Maximum depth to flatten")
    parser.add_argument(
        "--preserve-lists",
        action="store_true",
        help="Keep arrays as-is (default).",
    )
    parser.add_argument(
        "--index-lists",
        action="store_true",
        help="Flatten arrays by numeric index into keys.",
    )

    args = parser.parse_args(argv)

    # Validate mutually exclusive flags for list handling
    if args.preserve_lists and args.index_lists:
        print("Choose either --preserve-lists OR --index-lists (not both).", file=sys.stderr)
        return 2

    # Default: preserve lists
    preserve_lists = True
    if args.index_lists:
        preserve_lists = False

    # Read input JSON file
    with args.input.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    # Build the Pydantic request model
    req = FlattenRequest(
        data=raw,
        options=FlattenOptions(
            sep=args.sep,
            max_depth=args.max_depth,
            preserve_lists=preserve_lists,
        ),
    )

    # Perform flattening
    flat = flatten_to_dict(req).data

    # Write to file or print to stdout
    if args.output:
        with args.output.open("w", encoding="utf-8") as f:
            json.dump(flat, f, ensure_ascii=False, indent=2)
        print(f"Wrote flattened JSON to {args.output}")
    else:
        print(json.dumps(flat, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())