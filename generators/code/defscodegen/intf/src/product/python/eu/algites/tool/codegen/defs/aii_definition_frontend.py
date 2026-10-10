from __future__ import annotations

from typing import Protocol

from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind


class AIiDefinitionFrontend(Protocol):
    """Defines the contract for one canonical-definition source-format frontend."""

    @property
    def source_kind(self) -> AInDefinitionSourceKind:
        """Return the definition source kind handled by this frontend."""
        ...

    def load(self, request: AIcdDefinitionLoadRequest) -> AIcdCanonicalDefinition:
        """Load one source definition into the normalized canonical-definition model."""
        ...
