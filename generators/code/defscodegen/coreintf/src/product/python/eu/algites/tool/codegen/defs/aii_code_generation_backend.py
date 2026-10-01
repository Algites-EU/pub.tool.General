from __future__ import annotations

from typing import Protocol

from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.aicd_generated_source import AIcdGeneratedSource
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget


class AIiCodeGenerationBackend(Protocol):
    """Defines the contract for one generated-source target backend."""

    @property
    def target(self) -> AInCodeGenerationTarget:
        """Return the code-generation target handled by this backend."""
        ...

    def generate(self, request: AIcdCodeGenerationRequest) -> AIcdGeneratedSource:
        """Generate one source artifact from a normalized canonical definition."""
        ...
