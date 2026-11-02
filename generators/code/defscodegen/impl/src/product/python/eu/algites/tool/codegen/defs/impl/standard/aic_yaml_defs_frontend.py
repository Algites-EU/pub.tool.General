from __future__ import annotations

from eu.algites.tool.codegen.common.aix_codegen_validation_exception import AIxCodegenValidationException
from eu.algites.tool.codegen.defs.impl.standard._schema_loading import load_schema

import json
import yaml
from typing import Any, Mapping
from eu.algites.tool.codegen.defs.impl.standard.aic_json_schema_reader import AIcJsonSchemaReader
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind

class AIcYamlDefsFrontend:
    """Loads yaml defs definitions into the normalized canonical model."""
    source_kind = AInDefinitionSourceKind.YAMLDEFS

    def __init__(self):
        """Initialize this service instance."""
        self._reader = AIcJsonSchemaReader()

    def load(self, request):
        """Load one source definition into the normalized canonical-definition model."""
        if request.path.suffix.lower() == ".json":
            root = load_schema(request.path)
        else:
            root = load_schema(request.path)
        if not isinstance(root, Mapping):
            raise AIxCodegenValidationException("yamldefs definition root must be a mapping", 'Check the collection shape, entry type, key definition and key field paths. Use a complete, resolvable key or declare the intended virtual map property key explicitly.')
        profile = request.source_naming_profile
        catalog = request.naming_profile
        if not profile or catalog is None or profile not in catalog.names:
            raise AIxCodegenValidationException(f'Missing configured {self.source_kind} source naming convention: {request.path}', 'Select the appropriate naming catalog/profile and check its configured structure rules. Rename the source declaration to match that profile or update the profile explicitly.')
        fields = catalog.schema_metadata_fields(profile) if profile else {}
        return self._reader.read(root, request, self.source_kind,
            fields.get('schema_source_schema_identifier', ''),
            fields.get('schema_source_schema_version', ''),
            'x-yamldefs-name',
            fields.get('schema_source_schema_url', ''))
