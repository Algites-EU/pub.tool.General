from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from eu.algites.lib.naming.convention.aicd_naming_profile import AIcdNamingProfile
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind

@dataclass(frozen=True, slots=True)
class AIcdDefinitionLoadRequest:
    """Carries immutable definition load request data.

    Attributes:
        path: Source definition path.
        source_kind: Definition source family.
        naming_profile: Naming/version profile.
    """
    path: Path
    source_kind: AInDefinitionSourceKind
    naming_profile: AIcdNamingProfile
