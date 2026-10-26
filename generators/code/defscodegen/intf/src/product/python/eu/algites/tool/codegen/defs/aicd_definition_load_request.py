from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1 import AIcNameConventionCatalog_1
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
    naming_profile: AIcNameConventionCatalog_1
    source_naming_profile: str = ""
