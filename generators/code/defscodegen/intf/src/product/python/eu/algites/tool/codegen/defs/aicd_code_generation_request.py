from __future__ import annotations

from dataclasses import dataclass
from eu.algites.tool.codegen.defs.aicd_canonical_definition import AIcdCanonicalDefinition
from eu.algites.lib.naming.convention.impl.algites.aic_name_convention_catalog_1 import AIcNameConventionCatalog_1
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget

@dataclass(frozen=True, slots=True)
class AIcdCodeGenerationRequest:
    """Carries immutable code generation request data.

    Attributes:
        definition: Normalized canonical definition.
        target: Target programming technology.
        package_name: Target package/module namespace.
        naming_profile: Naming/version profile.
        xml_type_qname: Optional expanded QName of a named XSD type, distinct
            from any global element name and omitted for other schema families.
        naming_convention: Exact selected naming catalog identifier, independent of its syntax.
        contract_role: Semantic role of the generated contract.
    """
    definition: AIcdCanonicalDefinition
    target: AInCodeGenerationTarget
    package_name: str
    naming_profile: AIcNameConventionCatalog_1
    xml_type_qname: str | None = None
    naming_convention: str = ''
    contract_role: str = ''

    def __post_init__(self):
        """Reject inconsistent XML identity instead of emitting misleading metadata."""
        from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
        if self.xml_type_qname is not None and (self.definition.source_kind is not AInDefinitionSourceKind.XMLDEFS
                or not self.xml_type_qname.startswith('{') or '}' not in self.xml_type_qname[1:]
                or self.xml_type_qname.endswith('}')):
            raise ValueError('Expected expanded QName of a named XML Schema type')
