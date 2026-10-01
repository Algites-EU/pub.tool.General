from __future__ import annotations

from dataclasses import dataclass
from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.lib.naming.convention.aicd_naming_profile import AIcdNamingProfile
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget

@dataclass(frozen=True, slots=True)
class AIcdCodeGenerationRequest:
    """Carries immutable code generation request data.

    Attributes:
        definition: Normalized canonical definition.
        target: Target programming technology.
        package_name: Target package/module namespace.
        naming_profile: Naming/version profile.
    """
    definition: AIcdCanonicalDefinition
    target: AInCodeGenerationTarget
    package_name: str
    naming_profile: AIcdNamingProfile
