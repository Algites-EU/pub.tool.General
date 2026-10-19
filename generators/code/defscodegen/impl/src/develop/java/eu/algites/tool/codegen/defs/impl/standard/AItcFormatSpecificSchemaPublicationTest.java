package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AIcdValueConstraints;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import java.util.List;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Cross-format $schema publication URLs must not masquerade as incompatible schema fields. */
public final class AItcFormatSpecificSchemaPublicationTest {
    private static AIcdCanonicalDefinition definition(AInDefinitionSourceKind aKind, String aUri,
            String aSource, String aValueType) {
        var locSchema = new AIcdPropertyDefinition("$schema", AIcSourceDataType.fromSourceHints(AInDataTypeKind.STRING, null, null, new AIcdValueConstraints("string", null, null,
                false, false, null, null, null, List.of(aUri)), AIcdValueConstraints.empty()), ((false) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, "Publication metadata", "$schema", null);
        var locValue = new AIcdPropertyDefinition("Name", AIcSourceDataType.fromSourceHints("integer".equals(aValueType)
                ? AInDataTypeKind.INTEGER : AInDataTypeKind.STRING, null, null, AIcdValueConstraints.empty(), AIcdValueConstraints.empty()), ((true) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, null, null, null);
        return new AIcdCanonicalDefinition("urn:customer", 1, "customer", aKind, aSource, "Test", AIcdDataType.object(List.of(locSchema, locValue)), List.of(), "Customer");
    }

    /** The field constraint is source-specific; the common AIig contract cannot impose one URL. */
    @Test
    public void AIcMergeSelfPublicationSchemaAcrossFormats() {
        var locJson = definition(AInDefinitionSourceKind.JSONDEFS,
                "https://defs.dev.algites.eu/api/jsondefs/example/customer_1.jsondef.schema.json",
                "artifact/src/product/jsondefs/example/customer_1.jsondef.schema.json", "string");
        var locYaml = definition(AInDefinitionSourceKind.YAMLDEFS,
                "https://defs.dev.algites.eu/api/yamldefs/example/customer_1.yamldef.schema.json",
                "artifact/src/product/yamldefs/example/customer_1.yamldef.schema.json", "string");
        var locMerged = AIcCanonicalDefinitionMerger.AIcMerge(List.of(locJson, locYaml));
        Assert.assertTrue(locMerged.dataType().properties().get(0).dataType().constraints().enumValues().isEmpty());
        Assert.assertEquals(locMerged.dataType().properties().get(1).dataType().kind(), AInDataTypeKind.STRING);
        /* Gradle stores the same relative source location without a leading artifact directory. */
        var locRootRelative = new AIcdCanonicalDefinition(locYaml.identity(), locYaml.version(), locYaml.logicalName(), locYaml.sourceKind(), locYaml.sourceResource().substring("artifact/".length()), locYaml.description(), locYaml.dataType(), locYaml.enumValues(), locYaml.title());
        var locRootJson = new AIcdCanonicalDefinition(locJson.identity(), locJson.version(), locJson.logicalName(), locJson.sourceKind(), locJson.sourceResource().substring("artifact/".length()), locJson.description(), locJson.dataType(), locJson.enumValues(), locJson.title());
        Assert.assertTrue(AIcCanonicalDefinitionMerger.AIcMerge(List.of(locRootJson, locRootRelative))
                .dataType().properties().get(0).dataType().constraints().enumValues().isEmpty());
    }

    /** A genuine const mismatch or changed data field must still be rejected. */
    @Test
    public void AIcRejectUnrelatedSchemaConstantOrChangedField() {
        var locJson = definition(AInDefinitionSourceKind.JSONDEFS,
                "https://defs.dev.algites.eu/api/jsondefs/example/customer_1.jsondef.schema.json",
                "artifact/src/product/jsondefs/example/customer_1.jsondef.schema.json", "string");
        var locUnrelated = definition(AInDefinitionSourceKind.YAMLDEFS,
                "https://other.example/foreign-schema",
                "artifact/src/product/yamldefs/example/customer_1.yamldef.schema.json", "string");
        var locChanged = definition(AInDefinitionSourceKind.YAMLDEFS,
                "https://defs.dev.algites.eu/api/yamldefs/example/customer_1.yamldef.schema.json",
                "artifact/src/product/yamldefs/example/customer_1.yamldef.schema.json", "integer");
        Assert.expectThrows(IllegalArgumentException.class,
                () -> AIcCanonicalDefinitionMerger.AIcMerge(List.of(locJson, locUnrelated)));
        Assert.expectThrows(IllegalArgumentException.class,
                () -> AIcCanonicalDefinitionMerger.AIcMerge(List.of(locJson, locChanged)));
    }
}
