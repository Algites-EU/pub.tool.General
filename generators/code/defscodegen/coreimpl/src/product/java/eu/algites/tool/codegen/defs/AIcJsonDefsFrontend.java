package eu.algites.tool.codegen.defs;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;

/** Default JSON-definition frontend. */
public final class AIcJsonDefsFrontend implements AIiDefinitionFrontend {
    /** Creates the default jsondefs frontend. */
    public AIcJsonDefsFrontend() {
    }
    private final ObjectMapper mapper = new ObjectMapper();
    private final AIcJsonSchemaReader reader = new AIcJsonSchemaReader();

    /**
     * Returns the source family handled by this frontend.
     *
     * @return the jsondefs source kind
     */
    @Override
    public AInDefinitionSourceKind sourceKind() {
        return AInDefinitionSourceKind.JSONDEFS;
    }

    /**
     * Loads one jsondefs resource into the format-neutral canonical-definition model.
     *
     * @param request source path and naming policy
     * @return normalized canonical definition
     * @throws IOException if the source cannot be read
     */
    @Override
    public AIcdCanonicalDefinition load(AIcdDefinitionLoadRequest request) throws IOException {
        JsonNode root = mapper.readTree(request.path().toFile());
        return reader.read(root, request, sourceKind(), "x-jsondefs-id", "x-jsondefs-version", "x-jsondefs-name");
    }
}
