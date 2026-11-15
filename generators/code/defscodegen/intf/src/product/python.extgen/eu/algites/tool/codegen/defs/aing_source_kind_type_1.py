from __future__ import annotations
from typing import Any

from enum import Enum


class AIngSourceKindType_1(str, Enum):
    """Selects the source-definition family handled by the frontend.

    Canonical identity: eu.algites.tool.codegen.defs.input-profile#/$defs/SourceKindType; version: 1.
    Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/input-profile_1.xsd}SourceKindType; version: 1."""

    YAMLDEFS = 'yamldefs'
    JSONDEFS = 'jsondefs'
    XMLDEFS = 'xmldefs'

    def code(self) -> str:
        """Return the exact typed wire code."""
        return self.value
