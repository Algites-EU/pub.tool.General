from __future__ import annotations

from typing import Protocol

from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.aicd_generated_source import AIcdGeneratedSource


class AIiDefsCodegenService(Protocol):
    """Defines the programmatic service contract for canonical-definition code generation."""

    def load(self, request: AIcdDefinitionLoadRequest) -> AIcdCanonicalDefinition:
        """Load one source definition into the normalized canonical-definition model."""
        ...

    def generate(self, request: AIcdCodeGenerationRequest) -> AIcdGeneratedSource:
        """Generate one source artifact from a normalized canonical definition."""
        ...
