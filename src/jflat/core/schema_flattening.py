"""
schema_flattening.py
=====================
A **single-file, runnable prototype** that demonstrates a didactic pipeline:

PDF_Extractor (stub) -> dict_raw_extraction (nested) -> SchemaFlattener -> flattened outputs.

It also supports **Pydantic v2 models** as input and generates a **flattened model-graph**
structure with the following conventions:

- One central registry: "$defs"
- For each model:
    - Primitive fields are listed as {"field": {"type": "str|int|..."}}
    - Composition (nested BaseModel fields) is recorded in "$contains":
        - entries like "field_name#/$defs/ModelName"
    - Inheritance is recorded in "$inherits_from":
        - value like "#/$defs/BaseModelName"

The module exposes a small CLI demo:

    python schema_flattening.py --demo

which prints two outputs:
1) `{ "$defs": { ... } }` (JSON-embeddable)
2) `{ ... }` (just the inner mapping, as explicitly requested by the user)

All code is **commented** for teaching purposes.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Type, get_args, get_origin
import json
import sys

try:
    # Pydantic v2 imports
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover
    BaseModel = object  # type: ignore
    def Field(*args, **kwargs):  # type: ignore
        return None

# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def _is_basemodel_subclass(tp: Any) -> bool:
    """Return True if *tp* is a (Pydantic) BaseModel subclass.

    Handles Optional[Model], Annotated[Model, ...], etc., by peeling typing wrappers.
    """
    if tp is None:
        return False

    origin = get_origin(tp)
    args = get_args(tp)

    # Unwrap Optional[T], list[T], Annotated[T, ...], etc., by checking typical origins
    if origin in (list, List, tuple, Tuple, Optional):
        if args:
            return any(_is_basemodel_subclass(a) for a in args)
        return False

    # Pydantic v2 BaseModel subclass check
    try:
        return isinstance(tp, type) and issubclass(tp, BaseModel) and (tp is not BaseModel)
    except Exception:
        return False


def _python_type_to_name(tp: Any) -> str:
    """Map python types to simple JSON-friendly type names.

    If *tp* is a typing wrapper (Optional, Annotated, etc.), try to reduce it to a base type.
    """
    origin = get_origin(tp)
    args = get_args(tp)

    # Reduce Optional[T] -> T, List[T] -> T, Annotated[T, ...] -> T
    if origin in (list, List, tuple, Tuple, Optional):
        if args:
            return _python_type_to_name(args[0])
        return "any"

    # Primitive/common types mapping
    mapping = {
        str: "str",
        int: "int",
        float: "float",
        bool: "bool",
        bytes: "bytes",
    }
    if tp in mapping:
        return mapping[tp]

    # Datetime-like: avoid importing heavy modules; use name fallback
    try:
        import datetime as _dt  # local import
        if tp in (_dt.date, _dt.datetime, _dt.time):
            return tp.__name__
    except Exception:
        pass

    # If it's a BaseModel subclass, refer to model name
    if _is_basemodel_subclass(tp):
        return tp.__name__

    # Fallback: best-effort readable name
    return getattr(tp, "__name__", str(tp))


# -----------------------------------------------------------------------------
# Abstract Input Adapter (validates input in __init__)
# -----------------------------------------------------------------------------

class InputAdapter(ABC):
    """Abstract adapter that validates input at construction.

    Subclasses normalize the input to an internal representation that the
    flattener can consume.
    """

    def __init__(self, data: Any) -> None:
        self.data = data
        self._validate()

    @abstractmethod
    def _validate(self) -> None:
        """Validate *self.data* (raise ValueError on invalid)."""
        ...

    @abstractmethod
    def to_model_graph(self) -> Dict[str, Dict[str, Any]]:
        """Return a *model graph* mapping: { ModelName: {"fields":..., "bases":...} }

        Shape per model entry:
            {
              "fields": { field_name: {"annotation": <py-type>, "description": str|None } },
              "bases": [ BaseModelSubclass, ... ]
            }
        """
        ...


# -----------------------------------------------------------------------------
# Pydantic Adapter: accepts Pydantic model classes and inspects them
# -----------------------------------------------------------------------------

class PydanticAdapter(InputAdapter):
    def _validate(self) -> None:
        # Accept a single BaseModel subclass, a list/tuple of them, or a module-like with attributes
        d = self.data

        def _collect_from_module(mod: Any) -> List[Type[BaseModel]]:
            out: List[Type[BaseModel]] = []
            for name in dir(mod):
                obj = getattr(mod, name)
                if isinstance(obj, type):
                    try:
                        if issubclass(obj, BaseModel) and obj is not BaseModel:
                            out.append(obj)
                    except Exception:
                        pass
            return out

        models: List[Type[BaseModel]] = []
        if isinstance(d, type):
            models = [d]
        elif isinstance(d, (list, tuple)):
            models = [m for m in d if isinstance(m, type)]
        else:
            # try module-like collector as fallback
            models = _collect_from_module(d)

        if not models:
            raise ValueError("PydanticAdapter expects BaseModel subclasses or a module containing them.")

        self.models = models

    def to_model_graph(self) -> Dict[str, Dict[str, Any]]:
        graph: Dict[str, Dict[str, Any]] = {}
        for model in self.models:
            fields: Dict[str, Dict[str, Any]] = {}
            # pydantic v2: model.model_fields
            mf = getattr(model, "model_fields", {})
            for fname, finfo in mf.items():
                ann = getattr(finfo, "annotation", Any)
                desc = getattr(finfo, "description", None)
                fields[fname] = {"annotation": ann, "description": desc}

            # collect BaseModel bases (for inheritance information)
            bases: List[Type[BaseModel]] = []
            for b in model.__bases__:
                try:
                    if issubclass(b, BaseModel) and b is not BaseModel:
                        bases.append(b)
                except Exception:
                    pass

            graph[model.__name__] = {"fields": fields, "bases": bases}
        return graph


# -----------------------------------------------------------------------------
# Dictionary (already-extracted) Adapter: accepts a nested dict and interprets it
# -----------------------------------------------------------------------------

class DictAdapter(InputAdapter):
    def _validate(self) -> None:
        if not isinstance(self.data, dict):
            raise ValueError("DictAdapter expects a dictionary.")

    def to_model_graph(self) -> Dict[str, Dict[str, Any]]:
        """Interpret a nested dictionary as a set of models.

        Expected shape example (very flexible for demo):
            {
                "Simulation": {
                    "fields": {
                        "name": {"type": str, "description": "..."},
                        "system": {"$model": "System"},
                    },
                    "bases": [],
                },
                "System": {
                    "fields": {
                        "name": {"type": str},
                    },
                    "bases": ["BaseSystem"],
                },
                "BaseSystem": { "fields": {"id": {"type": str}}, "bases": []}
            }
        The adapter is permissive; it treats `{ "type": <py-type>|"str" }` as primitives
        and `{ "$model": "ModelName" }` as a BaseModel composition.
        """
        raw: Dict[str, Any] = self.data
        graph: Dict[str, Dict[str, Any]] = {}

        for model_name, content in raw.items():
            fields_spec = content.get("fields", {}) if isinstance(content, dict) else {}
            bases_spec = content.get("bases", []) if isinstance(content, dict) else []

            # normalize fields into annotation-like data
            fields: Dict[str, Dict[str, Any]] = {}
            for fname, meta in fields_spec.items():
                if isinstance(meta, dict) and "$model" in meta:
                    # composition
                    fields[fname] = {"annotation": meta["$model"], "description": meta.get("description")}
                else:
                    # primitive
                    tp = meta.get("type", "any") if isinstance(meta, dict) else meta
                    fields[fname] = {"annotation": tp, "description": meta.get("description") if isinstance(meta, dict) else None}

            # normalize bases
            bases: List[Any] = list(bases_spec) if isinstance(bases_spec, (list, tuple)) else []

            graph[model_name] = {"fields": fields, "bases": bases}

        return graph


# -----------------------------------------------------------------------------
# Flattener
# -----------------------------------------------------------------------------

@dataclass
class FlattenOptions:
    include_defs_wrapper: bool = True  # if True, return {"$defs": {...}}; else return {...}


class SchemaFlattener:
    """Flatten a *model graph* (from an InputAdapter) into the requested structure.

    The result follows the conventions described at the top of this file.
    """

    def __init__(self, adapter: InputAdapter, options: Optional[FlattenOptions] = None) -> None:
        self.adapter = adapter
        self.options = options or FlattenOptions()

    def _normalize_annotation_to_str(self, ann: Any) -> Tuple[bool, str]:
        """Return (is_model, name) where:
            - is_model: True if this is another model reference (composition)
            - name:     "str|int|..." for primitives, or ModelName for model refs
        For DictAdapter, annotations can be strings model names.
        For PydanticAdapter, annotations are python types.
        """
        # If annotation is a string, assume it's a model name (dict adapter composition)
        if isinstance(ann, str):
            return True, ann

        if _is_basemodel_subclass(ann):
            return True, _python_type_to_name(ann)

        # Primitive or other typing
        return False, _python_type_to_name(ann)

    def flatten(self) -> Dict[str, Any]:
        graph = self.adapter.to_model_graph()
        defs: Dict[str, Any] = {}

        # Helper for inheritance: map model -> first BaseModel base name (if any)
        def _first_base_name(bases: List[Any]) -> Optional[str]:
            for b in bases:
                if isinstance(b, str):  # DictAdapter
                    return b
                try:
                    if issubclass(b, BaseModel) and b is not BaseModel:
                        return b.__name__
                except Exception:
                    pass
            return None

        for model_name, meta in graph.items():
            fields: Dict[str, Dict[str, Any]] = meta.get("fields", {})
            bases: List[Any] = meta.get("bases", [])

            out_entry: Dict[str, Any] = {"$contains": []}

            # Collect fields: primitives vs model-composition
            for fname, finfo in fields.items():
                ann = finfo.get("annotation")
                is_model, tname = self._normalize_annotation_to_str(ann)
                if is_model:
                    # composition reference
                    out_entry["$contains"].append(f"{fname}#/$defs/{tname}")
                else:
                    out_entry[fname] = {"type": tname}

            # Inheritance
            base_name = _first_base_name(bases)
            if base_name:
                out_entry["$inherits_from"] = f"#/$defs/{base_name}"

            defs[model_name] = out_entry

        if self.options.include_defs_wrapper:
            return {"$defs": defs}
        return defs


# -----------------------------------------------------------------------------
# Demo Pydantic models (from the whiteboard / prompt wording)
# -----------------------------------------------------------------------------

class BaseSystem(BaseModel):
    id: str = Field(..., description="Unique system identifier")

class System(BaseSystem):
    name: str = Field(..., description="System name")
    chem_formula: str = Field(..., description="Chemical formula")

class Person(BaseModel):
    name: str = Field(..., description="Person name")

class Method(BaseModel):
    name: str = Field(..., description="Method name")
    person: Person

class Simulation(BaseModel):
    name: str
    run_time: float
    run_time_unit: str
    system: System
    method: Method


# -----------------------------------------------------------------------------
# PDF_Extractor (stub): returns a nested dict resembling a raw extraction
# -----------------------------------------------------------------------------

class PDF_Extractor:
    """Simplified PDF extractor.

    For this prototype, we don't parse a real PDF; we expose a `extract()`
    method returning a *nested* dictionary as if parsed from a PDF. In a real
    project, you'd wire PyPDF2 or other libs to parse the document.
    """

    def __init__(self, source: Optional[str] = None) -> None:
        self.source = source  # could be a filepath or in-memory bytes

    def extract(self) -> Dict[str, Any]:
        # Synthetic nested structure for demo purposes only
        return {
            "Simulation": {
                "fields": {
                    "name": {"type": str},
                    "run_time": {"type": float},
                    "run_time_unit": {"type": str},
                    "system": {"$model": "System"},
                    "method": {"$model": "Method"},
                },
                "bases": [],
            },
            "BaseSystem": {
                "fields": {"id": {"type": str}},
                "bases": [],
            },
            "System": {
                "fields": {
                    "name": {"type": str},
                    "chem_formula": {"type": str},
                },
                "bases": ["BaseSystem"],
            },
            "Method": {
                "fields": {
                    "name": {"type": str},
                    "person": {"$model": "Person"},
                },
                "bases": [],
            },
            "Person": {
                "fields": {"name": {"type": str}},
                "bases": [],
            },
        }


# -----------------------------------------------------------------------------
# CLI Demo
# -----------------------------------------------------------------------------

def _demo() -> None:
    print("\n=== DEMO: Flatten from Pydantic models ===\n")
    padapter = PydanticAdapter([Simulation, System, BaseSystem, Method, Person])

    # 1) with $defs wrapper
    flt = SchemaFlattener(padapter, options=FlattenOptions(include_defs_wrapper=True))
    out_with_defs = flt.flatten()
    print(json.dumps(out_with_defs, indent=2))

    # 2) bare mapping (required by the prompt to also output)
    print("\n--- Bare mapping (no $defs wrapper) ---\n")
    flt2 = SchemaFlattener(padapter, options=FlattenOptions(include_defs_wrapper=False))
    out_bare = flt2.flatten()
    print(json.dumps(out_bare, indent=2))

    # 3) Simulate PDF extraction path using DictAdapter
    print("\n=== DEMO: Flatten from PDF_Extractor (DictAdapter) ===\n")
    raw = PDF_Extractor().extract()
    dadapter = DictAdapter(raw)
    flt3 = SchemaFlattener(dadapter, options=FlattenOptions(include_defs_wrapper=True))
    print(json.dumps(flt3.flatten(), indent=2))


def main(argv: List[str]) -> int:
    if "--demo" in argv:
        _demo()
        return 0

    # Default behavior: show short help
    print(
        "Usage: python schema_flattening.py --demo\n"
        "Runs a demo that prints the flattened structures (both variants)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
