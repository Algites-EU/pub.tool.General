package eu.algites.tool.codegen.defs.impl.standard;

import com.fasterxml.jackson.databind.ObjectMapper;
import eu.algites.lib.naming.convention.impl.algites.AIcAlgitesNamingProfiles_1;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.nio.file.Files;
import java.nio.file.Path;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Confirms local named unions and closed-object presence semantics in both schema formats. */
public final class AItcLocalDefinitionsPresenceProjectionTest {
    private static final ObjectMapper MAPPER = new ObjectMapper();

    /**
     * A local definition containing oneOf and a structurally equivalent anyOf
     * object assertion must retain its actual choice type and property minimum.
     */
    @Test
    public void AIcReferenceToNamedChoicePreservesRequiredPropertyUnion() throws Exception {
        String locSource = """
                {
                  "type": "object",
                  "properties": {"Title": {"$ref": "#/$defs/displayText"}},
                  "$defs": {"displayText": {"oneOf": [
                    {"type": "string", "minLength": 1},
                    {"type": "object", "additionalProperties": false,
                     "properties": {
                       "Text": {"type": "string", "minLength": 1},
                       "ResourceKey": {"type": "string", "minLength": 1}
                     },
                     "anyOf": [{"required": ["Text"]}, {"required": ["ResourceKey"]}]}
                  ]}}
                }
                """;
        Path locDirectory = Files.createTempDirectory("defs-local-presence-");
        for (AInDefinitionSourceKind locKind : new AInDefinitionSourceKind[] {
                AInDefinitionSourceKind.JSONDEFS, AInDefinitionSourceKind.YAMLDEFS}) {
            String locSuffix = locKind == AInDefinitionSourceKind.JSONDEFS
                    ? "jsondef.schema.json" : "yamldef.schema.json";
            Path locPath = locDirectory.resolve("security-bootstrap_1." + locSuffix);
            Files.writeString(locPath, locSource);
            var locRequest = new AIcdDefinitionLoadRequest(locPath, locKind,
                    AIcAlgitesNamingProfiles_1.javaProfile());
            var locDefinition = new AIcJsonSchemaReader().read(MAPPER.readTree(locSource), locRequest,
                    locKind, "x-algites-schema-id", "x-algites-schema-version", "x-algites-schema-name");
            var locReference = locDefinition.dataType().properties().get(0).dataType().reference();
            Assert.assertNotNull(locReference);
            Assert.assertEquals(locReference.targetDataType().kind(), AInDataTypeKind.ONE_OF);
            var locAlternatives = locReference.targetDataType().alternatives();
            Assert.assertEquals(locAlternatives.get(0).kind(), AInDataTypeKind.STRING);
            Assert.assertEquals(locAlternatives.get(1).kind(), AInDataTypeKind.OBJECT);
            Assert.assertEquals(locAlternatives.get(1).constraints().minProperties(), Integer.valueOf(1));
            Assert.assertEquals(locAlternatives.get(1).properties().size(), 2);
        }
    }
}
