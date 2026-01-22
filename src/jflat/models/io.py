# jflat/models/io.py
# Pydantic models define the input/output contracts and options for flattening.
# This gives type safety, validation, defaults, and clear JSON serialization.

from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class FlattenOptions(BaseModel):
    """
    Options controlling how flattening behaves.

    Attributes:
      sep:           separator between nested key parts, e.g., "director_name"
      max_depth:     limit flattening depth (None means unlimited)
      preserve_lists:
                     True  -> leave lists unchanged (stored as lists)
                     False -> flatten lists by numeric index into keys (e.g., items_0_id)
    """
    sep: str = Field("_", description="Separator for nested keys")
    max_depth: Optional[int] = Field(default=None, ge=1, description="Maximum nesting depth to flatten")
    preserve_lists: bool = Field(default=True, description="If False, lists are flattened by numeric index")

    @field_validator("sep")
    @classmethod
    def non_empty_sep(cls, v: str) -> str:
        # Ensure separator is at least one character to avoid ambiguous keys.
        if not v:
            raise ValueError("Separator cannot be empty")
        return v


class FlattenRequest(BaseModel):
    """
    Input contract for flattening.
    - data:    your nested JSON as a Python dict
    - options: behavior switches (separator, depth, list handling)
    """
    data: dict[str, Any] = Field(..., description="Nested JSON object")
    options: FlattenOptions = Field(default_factory=FlattenOptions)


class FlattenedDict(BaseModel):
    """
    Output contract for dict-style flattening.
    'data' is the resulting flat map.
    """
    data: dict[str, Any] = Field(..., description="Flat key-value map")


class FlattenResponse(BaseModel):
    """
    High-level response wrapper for future extensibility.
    Today, we only support mode='dict'.
    """
    mode: Literal["dict"] = "dict"
    result: FlattenedDict