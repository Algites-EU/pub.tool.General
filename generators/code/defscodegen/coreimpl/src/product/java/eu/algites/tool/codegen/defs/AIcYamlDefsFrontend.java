package eu.algites.tool.codegen.defs;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;

import java.io.IOException;

/** Default YAML-definition frontend with semantics independent from jsondefs. */
public final class AIcYamlDefsFrontend implements AIiDefinitionFrontend {
    /** Creates the default yamldefs frontend. */
    public AIcYamlDefsFrontend() {
    }
    private final ObjectMapper jsonMapper = new ObjectMapper().enable(com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
    private final ObjectMapper yamlMapper = new ObjectMapper(new YAMLFactory()).enable(com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
    private final AIcJsonSchemaReader reader = new AIcJsonSchemaReader();

    /**
     * Returns the source family handled by this frontend.
     *
     * @return the yamldefs source kind
     */
    @Override
    public AInDefinitionSourceKind sourceKind() {
        return AInDefinitionSourceKind.YAMLDEFS;
    }

    /**
     * Loads one yamldefs resource into the format-neutral canonical-definition model.
     *
     * @param request source path and naming policy
     * @return normalized canonical definition
     * @throws IOException if the source cannot be read
     */
    @Override
    public AIcdCanonicalDefinition load(AIcdDefinitionLoadRequest request) throws IOException {
        String fileName = request.path().getFileName().toString().toLowerCase();
        ObjectMapper mapper = fileName.endsWith(".json") ? jsonMapper : yamlMapper;
        JsonNode root = mapper.readTree(request.path().toFile());
        return reader.read(root, request, sourceKind(), "x-yamldefs-id", "x-yamldefs-version", "x-yamldefs-name");
    }
}
