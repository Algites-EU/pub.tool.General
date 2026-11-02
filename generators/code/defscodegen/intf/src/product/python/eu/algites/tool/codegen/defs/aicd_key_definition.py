"""Immutable canonical description of one unique or grouping key."""

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AIcdKeyDefinition:
    """One ordered key path extracted from collection item values.

    Attributes:
        name: Nonempty identity of the key, unique among collection definitions.
        fields: One or more typed field paths, ordered as in the source schema.
        unique: Whether duplicate complete keys are rejected.
        required: Whether incomplete keys violate the definition (xs:key versus xs:unique).
        virtual: Whether the key is supplied by its parent serialization object
            instead of stored as ordinary value fields (JSON/YAML object key).
    """

    name: str
    fields: tuple[str, ...]
    unique: bool = True
    virtual: bool = False
    required: bool = True

    def __post_init__(self) -> None:
        if not self.name or not self.fields or any(not path for path in self.fields):
            raise AIxCodegenValidationException('Canonical key needs a name and nonempty field paths', 'Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.')
        if self.virtual and len(self.fields) != 1:
            raise AIxCodegenValidationException('Virtual object-property key must be scalar', 'Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.')
        object.__setattr__(self, 'fields', tuple(self.fields))
