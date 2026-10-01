from __future__ import annotations

import json
import yaml
from typing import Any, Mapping
from eu.algites.tool.codegen.defs.aic_json_schema_reader import AIcJsonSchemaReader
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
            root = json.loads(request.path.read_text(encoding="utf-8"))
        else:
            root = yaml.safe_load(request.path.read_text(encoding="utf-8"))
        if not isinstance(root, Mapping):
            raise ValueError("yamldefs definition root must be a mapping")
        return self._reader.read(root, request, self.source_kind, "x-yamldefs-id", "x-yamldefs-version", "x-yamldefs-name")
