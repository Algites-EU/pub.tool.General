package eu.algites.tool.codegen.defs;


import java.io.IOException;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/** Default registry-backed defs-codegen service. */
public final class AIcDefaultDefsCodegenService implements AIiDefsCodegenService {
    private final Map<AInDefinitionSourceKind, AIiDefinitionFrontend> frontends = new EnumMap<>(AInDefinitionSourceKind.class);
    private final Map<AInCodeGenerationTarget, AIiCodeGenerationBackend> backends = new EnumMap<>(AInCodeGenerationTarget.class);

    /** Creates the service with the built-in yamldefs, jsondefs, xmldefs, Java, and Python providers. */
    public AIcDefaultDefsCodegenService() {
        this(List.of(new AIcYamlDefsFrontend(), new AIcJsonDefsFrontend(), new AIcXmlDefsFrontend()),
                List.of(new AIcJavaCodeGenerationBackend(), new AIcPythonCodeGenerationBackend()));
    }

    /**
     * Creates the service from explicit frontend and backend implementations.
     *
     * @param frontendList definition-format frontends to register
     * @param backendList code-generation backends to register
     */
    public AIcDefaultDefsCodegenService(List<AIiDefinitionFrontend> frontendList, List<AIiCodeGenerationBackend> backendList) {
        for (AIiDefinitionFrontend frontend : frontendList) frontends.put(frontend.sourceKind(), frontend);
        for (AIiCodeGenerationBackend backend : backendList) backends.put(backend.target(), backend);
    }

    /**
     * Loads one source definition through the frontend selected by its source kind.
     *
     * @param request definition load request
     * @return normalized canonical definition
     * @throws IOException if the selected frontend cannot load the source
     */
    @Override
    public AIcdCanonicalDefinition load(AIcdDefinitionLoadRequest request) throws IOException {
        AIiDefinitionFrontend frontend = frontends.get(request.sourceKind());
        if (frontend == null) throw new IllegalArgumentException("No frontend for " + request.sourceKind());
        return frontend.load(request);
    }

    /**
     * Generates one source artifact through the backend selected by its target technology.
     *
     * @param request code-generation request
     * @return generated source artifact
     */
    @Override
    public AIcdGeneratedSource generate(AIcdCodeGenerationRequest request) {
        AIiCodeGenerationBackend backend = backends.get(request.target());
        if (backend == null) throw new IllegalArgumentException("No backend for " + request.target());
        return backend.generate(request);
    }
}
