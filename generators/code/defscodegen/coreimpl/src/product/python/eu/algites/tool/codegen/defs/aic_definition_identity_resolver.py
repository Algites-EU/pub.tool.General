from __future__ import annotations

from eu.algites.lib.naming.conversion.aic_default_name_converter import AIcDefaultNameConverter
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs._support import _strip_extensions

class AIcDefinitionIdentityResolver:
    """Provides definition identity resolver functionality."""
    def __init__(self) -> None:
        """Initialize this service instance."""
        self.converter = AIcDefaultNameConverter()

    def from_file(self, request: AIcdDefinitionLoadRequest, explicit_version: int | None):
        """Resolve canonical logical identity and version from a definition file."""
        return self.converter.parse_versioned_name(
            _strip_extensions(request.path.name), explicit_version, request.naming_profile.input_version_policy
        )
