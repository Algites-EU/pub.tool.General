package eu.algites.tool.codegen.defs.impl.standard;


import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AIiDefinitionFrontend;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import eu.algites.lib.naming.convention.impl.algites.AIcNameConventionCatalog_1;
import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;

/** Default JSON-definition frontend. */
public final class AIcJsonDefsFrontend implements AIiDefinitionFrontend {
    /** Creates the default jsondefs frontend. */
    public AIcJsonDefsFrontend() {
    }
    private final ObjectMapper mapper = new ObjectMapper().enable(com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
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
        AIcNameConventionCatalog_1 locDefault = AIcNameConventionCatalog_1.loadResource("algites-jsondef-name-conventions.yml");
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
        return reader.read(root, request, sourceKind(), locId, locVersion, "x-jsondefs-name", locUrl);
    }
}
