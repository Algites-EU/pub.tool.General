from __future__ import annotations

import json
from eu.algites.tool.codegen.defs.aic_json_schema_reader import AIcJsonSchemaReader
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind

class AIcJsonDefsFrontend:
    """Loads json defs definitions into the normalized canonical model."""
    source_kind = AInDefinitionSourceKind.JSONDEFS

    def __init__(self):
        """Initialize this service instance."""
        self._reader = AIcJsonSchemaReader()

    def load(self, request):
        """Load one source definition into the normalized canonical-definition model."""
        root = json.loads(request.path.read_text(encoding="utf-8"))
        return self._reader.read(root, request, self.source_kind, "x-jsondefs-id", "x-jsondefs-version", "x-jsondefs-name")
