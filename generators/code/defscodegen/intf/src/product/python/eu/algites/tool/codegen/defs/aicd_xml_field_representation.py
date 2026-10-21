"""Format-specific XML wire identity for one canonical data-object property."""
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
            raise ValueError('XML field requires a namespace string and nonblank local name')
        if self.min_occurs < -1 or self.max_occurs < -1 or (
                self.min_occurs >= 0 and self.max_occurs >= 0 and self.min_occurs > self.max_occurs):
            raise ValueError('Invalid XML wire occurrence interval')
        if not isinstance(self.value_kind, AInXmlValueKind):
            raise ValueError('XML field requires an AInXmlValueKind')
        if self.wildcard_namespace and (self.value_kind is not AInXmlValueKind.ELEMENT
                or self.wildcard_process_contents not in ('skip', 'lax', 'strict')):
            raise ValueError('Invalid xs:any wildcard metadata')
