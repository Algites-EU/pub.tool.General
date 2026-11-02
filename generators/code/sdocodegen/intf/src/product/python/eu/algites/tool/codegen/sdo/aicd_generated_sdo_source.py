"""One generated SmartDataObject source with its importable type identity."""

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
from dataclasses import dataclass


@dataclass(frozen=True)
class AIcdGeneratedSdoSource:
    """Describes a generated SDO source unit and its importable type identity."""
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
        """Return the source identity, rejecting absent fully qualified type information."""
        if not self.fully_qualified_type_name:
            raise AIxCodegenValidationException('Generated SDO type identity is missing', 'Inspect the indicated schema declaration, its source metadata and field types. Correct the invalid name, requiredness, type or version at that source rather than editing generated files.')
        return self
