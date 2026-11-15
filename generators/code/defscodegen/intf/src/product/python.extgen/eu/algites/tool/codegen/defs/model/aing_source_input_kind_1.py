from __future__ import annotations
from typing import Any

from enum import Enum


class AIngSourceInputKind_1(str, Enum):
    """Schema language provenance

    Canonical identity: eu.algites.tool.codegen.defs.model.canonical-model#/$defs/SourceInputKind; version: 1.
    Equivalent schema identity: {https://defs.dev.algites.eu/api/xmldefs/eu/algites/tool/codegen/defs/model/canonical-model_1.xsd}SourceInputKind; version: 1."""

    XMLDEFS = 'XMLDEFS'
    YAMLDEFS = 'YAMLDEFS'
    JSONDEFS = 'JSONDEFS'

    def code(self) -> str:
        """Return the exact typed wire code."""
        return self.value
