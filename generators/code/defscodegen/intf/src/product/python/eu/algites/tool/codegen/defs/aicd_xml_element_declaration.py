"""Global XML element declaration, distinct from its named data type."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AIcdXmlElementDeclaration:
    """Identity, content type and direct substitution relation of a global XSD element."""
    local_name: str
    namespace: str
    type_qname: str
    substitution_head_qname: str | None = None
    abstract_element: bool = False
    nillable: bool = False

    @property
    def qname(self) -> str:
        """Expanded XML QName, independent of lexical prefix."""
        return '{' + self.namespace + '}' + self.local_name
