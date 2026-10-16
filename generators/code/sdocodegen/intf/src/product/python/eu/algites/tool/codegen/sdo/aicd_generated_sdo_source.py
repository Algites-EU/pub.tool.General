"""One generated SmartDataObject source with its importable type identity."""
from dataclasses import dataclass


@dataclass(frozen=True)
class AIcdGeneratedSdoSource:
    type_name: str
    relative_path: str
    source: str
    namespace: str = ''
    module_name: str = ''
    fully_qualified_type_name: str = ''
    type_role: str = ''
    source_definition_id: str = ''
    source_definition_version: int | None = None

    @property
    def primary_type(self):
        if not self.fully_qualified_type_name:
            raise ValueError('Generated SDO type identity is missing')
        return self
