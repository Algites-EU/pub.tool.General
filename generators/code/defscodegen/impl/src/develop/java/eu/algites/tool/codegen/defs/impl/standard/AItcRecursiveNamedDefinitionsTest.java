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

/**
 * Prevents a recursive local schema contract from causing unbounded expansion
 * when both Java and Python code generators read named JSON Schema references.
 * A recursive object or choice must remain nominal; a circular inline alias
 * without a named target is rejected with a controlled diagnostic.
 */
public final class AItcRecursiveNamedDefinitionsTest {
    /** A recursive named object must keep its array member as a reference to itself. */
    @Test
    public void AIcRecursiveFinalizationActionsKeepNamedReference() throws Exception {
        String locSchema = """
                {"type":"object","properties":{"Action":{"$ref":"#/$defs/FinalizationAction"}},
                 "$defs":{"FinalizationAction":{"type":"object","properties":{
                   "Id":{"type":"string"},
                   "FinalizationActions":{"type":"array","items":{"$ref":"#/$defs/FinalizationAction"}}
                 }}}}
                """;
        Path locSchemaFile = Files.createTempDirectory("recursive-finalization-").resolve("recursive-finalization_1.jsondef.schema.json");
        Files.writeString(locSchemaFile, locSchema);
        var locRequest = new AIcdDefinitionLoadRequest(locSchemaFile,
                AInDefinitionSourceKind.JSONDEFS, AIcAlgitesNamingProfiles_1.javaProfile());
        var locResult = new AIcJsonSchemaReader().read(new ObjectMapper().readTree(locSchema),
                locRequest, AInDefinitionSourceKind.JSONDEFS,
                "x-jsondefs-id", "x-jsondefs-version", "x-jsondefs-name");
        var locAction = locResult.dataType().properties().get(0).dataType();
        Assert.assertEquals(locAction.kind(), AInDataTypeKind.REFERENCE);
        Assert.assertEquals(locAction.reference().logicalName(),
                "recursive-finalization-definition-finalization-action");
        Assert.assertEquals(locAction.reference().targetDataType().kind(), AInDataTypeKind.OBJECT);
    }

    /** A recursive named choice keeps the first union shape and closes its back edge nominally. */
    @Test
    public void AIcRecursiveNamedChoicePreservesAlternatives() throws Exception {
        String locSchema = """
                {"type":"object","properties":{"Value":{"$ref":"#/$defs/Node"}},
                 "$defs":{"Node":{"oneOf":[{"type":"string"},{"type":"object","properties":{
                   "Next":{"$ref":"#/$defs/Node"}}}]}}}
                """;
        Path locPath = Files.createTempDirectory("recursive-choice-").resolve("recursive-choice_1.jsondef.schema.json");
        Files.writeString(locPath, locSchema);
        var locRequest = new AIcdDefinitionLoadRequest(locPath,
                AInDefinitionSourceKind.JSONDEFS, AIcAlgitesNamingProfiles_1.javaProfile());
        var locResult = new AIcJsonSchemaReader().read(new ObjectMapper().readTree(locSchema),
                locRequest, AInDefinitionSourceKind.JSONDEFS,
                "x-jsondefs-id", "x-jsondefs-version", "x-jsondefs-name");
        var locUnion = locResult.dataType().properties().get(0).dataType().reference().targetDataType();
        Assert.assertEquals(locUnion.kind(), AInDataTypeKind.ONE_OF);
        Assert.assertEquals(locUnion.alternatives().get(0).kind(), AInDataTypeKind.STRING);
        var locBackEdge = locUnion.alternatives().get(1).properties().get(0).dataType();
        Assert.assertEquals(locBackEdge.kind(), AInDataTypeKind.REFERENCE);
        Assert.assertNull(locBackEdge.reference().targetDataType());
    }

    /** Circular aliases without a nominal object or union fail explicitly, never by stack overflow. */
    @Test
    public void AIcCircularInlineAliasProducesDiagnostic() throws Exception {
        String locSchema = """
                {"type":"object","properties":{"Value":{"$ref":"#/$defs/alias"}},
                 "$defs":{"alias":{"$ref":"#/$defs/alias"}}}
                """;
        Path locPath = Files.createTempDirectory("recursive-alias-").resolve("recursive-alias_1.jsondef.schema.json");
        Files.writeString(locPath, locSchema);
        var locRequest = new AIcdDefinitionLoadRequest(locPath,
                AInDefinitionSourceKind.JSONDEFS, AIcAlgitesNamingProfiles_1.javaProfile());
        var locNode = new ObjectMapper().readTree(locSchema);
        var locFailure = Assert.expectThrows(IllegalArgumentException.class,
                () -> new AIcJsonSchemaReader().read(locNode,
                        locRequest, AInDefinitionSourceKind.JSONDEFS,
                        "x-jsondefs-id", "x-jsondefs-version", "x-jsondefs-name"));
        Assert.assertTrue(locFailure.getMessage().contains("Circular inline schema alias"));
    }
}
