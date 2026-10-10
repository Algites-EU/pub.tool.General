from __future__ import annotations

from dataclasses import dataclass
from eu.algites.tool.codegen.defs.aicd_enum_value_definition import AIcdEnumValueDefinition
from eu.algites.tool.codegen.defs.aicd_property_definition import AIcdPropertyDefinition
from eu.algites.tool.codegen.defs.ain_definition_kind import AInDefinitionKind
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind

@dataclass(frozen=True, slots=True)
class AIcdCanonicalDefinition:
    """Carries immutable canonical definition data.

    Attributes:
        identity: Canonical definition identity.
        version: Canonical definition version.
        logical_name: Logical name without its version suffix.
        kind: Normalized definition kind.
        source_kind: Definition source family.
        source_resource: Canonical source resource path.
        description: Human-readable description.
        properties: Normalized object properties.
        enum_values: Canonical enum wire values together with their documentation.
    """
    identity: str
    version: int | None
    logical_name: str
    kind: AInDefinitionKind
    source_kind: AInDefinitionSourceKind
    source_resource: str
    description: str | None = None
    properties: tuple[AIcdPropertyDefinition, ...] = ()
    enum_values: tuple[AIcdEnumValueDefinition, ...] = ()
