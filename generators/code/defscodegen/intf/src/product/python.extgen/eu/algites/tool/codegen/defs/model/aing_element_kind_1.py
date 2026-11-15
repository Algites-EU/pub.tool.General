from __future__ import annotations
from typing import Any

from enum import Enum


class AIngElementKind_1(str, Enum):
    """Serialized field with a wire name (REFERENCED) or inline, unnamed structural group (EMBEDDED); independent of TypeOrigin.

    Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ElementKind; version: 1.
    Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}ElementKind; version: 1."""

    REFERENCED = 'REFERENCED'
    EMBEDDED = 'EMBEDDED'

    def code(self) -> str:
        """Return the exact typed wire code."""
        return self.value
