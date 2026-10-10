from __future__ import annotations

from dataclasses import dataclass
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind

@dataclass(frozen=True, slots=True)
class AIcdDefinitionReference:
    """Carries immutable definition reference data.

    Attributes:
        identity: Canonical definition identity.
        version: Canonical definition version.
        logical_name: Logical name without its version suffix.
        target_kind: Referenced definition kind.
    """
    identity: str
    version: int | None
    logical_name: str
    target_kind: AInDefinitionKind | None = None
