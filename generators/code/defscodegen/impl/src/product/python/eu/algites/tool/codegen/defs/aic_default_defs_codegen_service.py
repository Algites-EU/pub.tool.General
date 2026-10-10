from __future__ import annotations

from eu.algites.tool.codegen.defs.aic_java_code_generation_backend import AIcJavaCodeGenerationBackend
from eu.algites.tool.codegen.defs.aic_json_defs_frontend import AIcJsonDefsFrontend
from eu.algites.tool.codegen.defs.aic_python_code_generation_backend import AIcPythonCodeGenerationBackend
from eu.algites.tool.codegen.defs.aic_xml_defs_frontend import AIcXmlDefsFrontend
from eu.algites.tool.codegen.defs.aic_yaml_defs_frontend import AIcYamlDefsFrontend

class AIcDefaultDefsCodegenService:
    """Provides default defs codegen service functionality."""
    def __init__(self, frontends=None, backends=None):
        """Initialize this service instance."""
        frontends = frontends or (AIcYamlDefsFrontend(), AIcJsonDefsFrontend(), AIcXmlDefsFrontend())
        backends = backends or (AIcJavaCodeGenerationBackend(), AIcPythonCodeGenerationBackend())
        self._frontends = {frontend.source_kind: frontend for frontend in frontends}
        self._backends = {backend.target: backend for backend in backends}

    def load(self, request):
        """Load one source definition into the normalized canonical-definition model."""
        return self._frontends[request.source_kind].load(request)

    def generate(self, request):
        """Generate one source artifact from a normalized canonical definition."""
        return self._backends[request.target].generate(request)
