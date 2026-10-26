package eu.algites.tool.codegen.defs.impl.standard;


import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AIiDefinitionFrontend;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import eu.algites.lib.naming.convention.impl.algites.AIcNameConventionCatalog_1;
import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
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
        AIcNameConventionCatalog_1 locDefault = AIcNameConventionCatalog_1.loadResource("algites-yamldef-name-conventions.yml");
        String locProfile = request.sourceNamingProfile();
        AIiNameConventionCatalog locCatalog = request.namingProfile();
        if (locProfile.isBlank()) {
            var locMatch = locDefault.recognizeFilename(request.path().getFileName().toString(), null);
            locProfile = locMatch == null ? "" : locMatch.conventionName();
            locCatalog = locDefault;
        } else if (!locCatalog.names().contains(locProfile)) {
            if (!locDefault.names().contains(locProfile))
                throw new IllegalArgumentException("Unknown source naming profile: " + locProfile);
            locCatalog = locDefault;
        }
        String locId = locProfile.isEmpty() ? "" : locCatalog.schemaMetadataField(locProfile, "schema_source", "identifier");
        String locVersion = locProfile.isEmpty() ? "" : locCatalog.schemaMetadataField(locProfile, "schema_source", "version");
        String locUrl = locProfile.isEmpty() ? "" : locCatalog.schemaMetadataField(locProfile, "schema_source", "url");
        return reader.read(root, request, sourceKind(), locId, locVersion, "x-yamldefs-name", locUrl);
    }
}
