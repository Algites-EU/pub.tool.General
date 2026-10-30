"""Immutable canonical description of one unique or grouping key."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AIcdKeyDefinition:
    """One ordered key path extracted from collection item values.

    Attributes:
        name: Nonempty identity of the key, unique among collection definitions.
        fields: One or more typed field paths, ordered as in the source schema.
        unique: Whether duplicate complete keys are rejected.
        virtual: Whether the key is supplied by its parent serialization object
            instead of stored as ordinary value fields (JSON/YAML object key).
    """

    name: str
    fields: tuple[str, ...]
    unique: bool = True
    virtual: bool = False

    def __post_init__(self) -> None:
        if not self.name or not self.fields or any(not path for path in self.fields):
            raise ValueError('Canonical key needs a name and nonempty field paths')
        if self.virtual and len(self.fields) != 1:
            raise ValueError('Virtual object-property key must be scalar')
        object.__setattr__(self, 'fields', tuple(self.fields))
