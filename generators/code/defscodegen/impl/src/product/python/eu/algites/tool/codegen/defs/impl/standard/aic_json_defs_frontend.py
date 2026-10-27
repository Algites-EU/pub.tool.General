from __future__ import annotations
from eu.algites.tool.codegen.defs.impl.standard._schema_loading import load_schema

import json
from eu.algites.tool.codegen.defs.impl.standard.aic_json_schema_reader import AIcJsonSchemaReader
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind

class AIcJsonDefsFrontend:
    """Loads json defs definitions into the normalized canonical model."""
    source_kind = AInDefinitionSourceKind.JSONDEFS

    def __init__(self):
        """Initialize this service instance."""
        self._reader = AIcJsonSchemaReader()

    def load(self, request):
        """Load one source definition into the normalized canonical-definition model."""
        root = load_schema(request.path)
        profile = request.source_naming_profile
        catalog = request.naming_profile
        if not profile or catalog is None or profile not in catalog.names:
            raise ValueError(f'Missing configured {self.source_kind} source naming convention: {request.path}')
        fields = catalog.schema_metadata_fields(profile) if profile else {}
        return self._reader.read(root, request, self.source_kind,
            fields.get('schema_source_schema_identifier', ''),
            fields.get('schema_source_schema_version', ''),
            'x-jsondefs-name',
            fields.get('schema_source_schema_url', ''))
