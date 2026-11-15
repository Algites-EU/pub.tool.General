from __future__ import annotations
from typing import Any

from enum import Enum


class AIngResolutionState_1(str, Enum):
    """Temporary resolution state on TYPE; only RESOLVED survives finalization

    Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/ResolutionState; version: 1.
    Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}ResolutionState; version: 1."""

    RESOLVED = 'RESOLVED'
    REFERENCE = 'REFERENCE'
    UNDEFINED = 'UNDEFINED'

    def code(self) -> str:
        """Return the exact typed wire code."""
        return self.value
