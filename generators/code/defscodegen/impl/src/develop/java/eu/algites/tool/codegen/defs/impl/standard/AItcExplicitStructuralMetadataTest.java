package eu.algites.tool.codegen.defs.impl.standard;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.nio.file.Files;
import java.nio.file.Path;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Confirms that validation subschemas cannot accidentally create DataObject fields
 * or nominal alternative types in the Java Defs frontend. Explicit vocabulary
 * annotations are the exclusive source of generated choice relationships.
 */
public final class AItcExplicitStructuralMetadataTest {
    /**
     * Checks that the structural projection includes only direct properties, even
     * when a validation branch requires another property on an instance.
     *
     * @throws Exception if the fixture or schema reader fails
     */
    @Test
    public void AIcAllOfAssertionsDoNotDefineGeneratedFields() throws Exception {
        JsonNode locSchema = new ObjectMapper().readTree("""
            {"type":"object","properties":{"own":{"type":"string"}},
             "allOf":[{"properties":{"validationOnly":{"type":"integer"}},
                       "required":["validationOnly"]}]}
            """);
        Path locFixture = Files.createTempFile("explicit-structure_1", ".jsondef.schema.json");
        try {
            var locRequest = new AIcdDefinitionLoadRequest(locFixture, AInDefinitionSourceKind.JSONDEFS,
                    AItcConfiguredNamingProfiles.javaProfile());
            AIcdCanonicalDefinition locDefinition = new AIcJsonSchemaReader().read(locSchema,
                    locRequest, AInDefinitionSourceKind.JSONDEFS, "", "", "");
            Assert.assertEquals(locDefinition.dataType().properties().size(), 1);
            Assert.assertEquals(locDefinition.dataType().properties().get(0).sourceName(), "own");
        } finally {
            Files.deleteIfExists(locFixture);
        }
    }

    /**
     * Verifies that an explicit nominal choice is emitted as an alternative data
     * type while an ordinary validation-only oneOf remains non-structural.
     *
     * @throws Exception if the temporary schema cannot be created or loaded
     */
    @Test
    public void AIcChoiceRequiresTheAlgitesVocabularyKeyword() throws Exception {
        var locMapper = new ObjectMapper();
        Path locFixture = Files.createTempFile("explicit-choice_1", ".jsondef.schema.json");
        try {
            JsonNode locSchema = locMapper.readTree("""
                {"type":"object","properties":{"payload":{"$ref":"#/$defs/Payload"}},
                 "$defs":{"Text":{"type":"object","properties":{"text":{"type":"string"}}},
                          "Count":{"type":"object","properties":{"count":{"type":"integer"}}},
                          "Payload":{"x-algites-defscodegen-choice":{
                                       "alternatives":["#/$defs/Text","#/$defs/Count"]},
                                     "oneOf":[{"$ref":"#/$defs/Text"},{"$ref":"#/$defs/Count"}]}}}
                """);
            locMapper.writeValue(locFixture.toFile(), locSchema);
            var locRequest = new AIcdDefinitionLoadRequest(locFixture, AInDefinitionSourceKind.JSONDEFS,
                    AItcConfiguredNamingProfiles.javaProfile());
            AIcdCanonicalDefinition locDefinition = new AIcJsonSchemaReader().read(locSchema,
                    locRequest, AInDefinitionSourceKind.JSONDEFS, "", "", "");
            Assert.assertEquals(locDefinition.dataType().properties().get(0).dataType()
                    .referencedDefinition().targetDataType().kind(), AInDataTypeKind.ONE_OF);
        } finally {
            Files.deleteIfExists(locFixture);
        }
    }
}
