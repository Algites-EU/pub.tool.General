"""Format-specific XML wire identity for one canonical data-object property."""

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
from dataclasses import dataclass
from eu.algites.lib.data.dataobject.xmldefs.ain_xml_value_kind import AInXmlValueKind


@dataclass(frozen=True, slots=True)
class AIcdXmlFieldRepresentation:
    """Preserve expanded QName and element/attribute kind independently of the field name."""
    namespace: str
    namespace_local_name: str
    value_kind: AInXmlValueKind
    min_occurs: int = -1
    max_occurs: int = -1
    wildcard_namespace: str = ''
    wildcard_process_contents: str = 'strict'

    def __post_init__(self):
        """Reject incomplete XML names and representation kinds."""
        if self.namespace is None or not self.namespace_local_name or not self.namespace_local_name.strip():
            raise AIxCodegenValidationException('XML field requires a namespace string and nonblank local name', 'Check the XSD targetNamespace, imported namespaces and QName/XPath prefixes. Ensure the referenced declaration exists and uses the expected namespace.')
        if self.min_occurs < -1 or self.max_occurs < -1 or (
                self.min_occurs >= 0 and self.max_occurs >= 0 and self.min_occurs > self.max_occurs):
            raise AIxCodegenValidationException('Invalid XML wire occurrence interval', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        if not isinstance(self.value_kind, AInXmlValueKind):
            raise AIxCodegenValidationException('XML field requires an AInXmlValueKind', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
        if self.wildcard_namespace and (self.value_kind is not AInXmlValueKind.ELEMENT
                or self.wildcard_process_contents not in ('skip', 'lax', 'strict')):
            raise AIxCodegenValidationException('Invalid xs:any wildcard metadata', 'Review the referenced XML Schema declaration and its XSD type, element and attribute definitions. Correct the unsupported or inconsistent schema construct.')
