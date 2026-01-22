
# jflat/core/schema_base.py
"""
This module defines an abstract interface (contract) for schema flatteners.

Why do we use an abstract base class (ABC)?
- It forces all flatteners to provide the same methods.
- It helps maintainability: new flatteners must match the same API.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class AbstractSchemaFlattener(ABC):
    """
    Abstract interface for a class that accepts a JSON schema (dict)
    and provides a flattened representation.
    """

    def __init__(self, schema_or_source: Any) -> None:
        """
        Concrete classes must validate input in __init__.

        schema_or_source can be:
        - a dict containing a JSON schema (Pydantic schema)
        - or something else (e.g. Pydantic model/class) depending on implementation
        """
        self._schema: dict[str, Any] = self._validate_and_build_schema(schema_or_source)

    @abstractmethod
    def _validate_and_build_schema(self, schema_or_source: Any) -> dict[str, Any]:
        """Validate input and return a JSON schema dictionary."""
        raise NotImplementedError

    @abstractmethod
    def flatten(self) -> dict[str, Any]:
        """Return the flattened dictionary in the requested output format."""
        raise NotImplementedError

    @abstractmethod
    def to_json(self, *, indent: int = 2) -> str:
        """Return a JSON string version (must be JSON-serializable)."""
        raise NotImplementedError
