from __future__ import annotations
from typing import Any

from enum import Enum


class AIngTypeOrigin_1(str, Enum):
    """Declared or synthesized during schema loading

    Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/TypeOrigin; version: 1.
    Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}TypeOrigin; version: 1."""

    DECLARED = 'DECLARED'
    SYNTHETIC = 'SYNTHETIC'

    def code(self) -> str:
        """Return the exact typed wire code."""
        return self.value
