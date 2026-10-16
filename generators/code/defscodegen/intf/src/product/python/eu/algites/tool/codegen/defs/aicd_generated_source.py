from __future__ import annotations

from dataclasses import dataclass
from eu.algites.tool.codegen.defs.aicd_generated_type_identity import AIcdGeneratedTypeIdentity


@dataclass(frozen=True, slots=True)
class AIcdGeneratedSource:
    """A source unit and its explicitly identified generated public types.

    ``generated_types`` describes importable declarations; callers must not
    reconstruct names from a source file or from source text. The default is
    retained for older producers and non-type source units.
    """

    type_name: str
    relative_path: str
    source: str
    generated_types: tuple[AIcdGeneratedTypeIdentity, ...] = ()

    @property
    def primary_type(self) -> AIcdGeneratedTypeIdentity:
        for entry in self.generated_types:
            if entry.type_name == self.type_name:
                return entry
        raise ValueError(f'No generated type identity for {self.type_name}')
