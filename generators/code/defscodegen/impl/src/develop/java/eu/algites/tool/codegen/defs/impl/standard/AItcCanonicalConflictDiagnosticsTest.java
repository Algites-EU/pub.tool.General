package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIcdDefinitionReference;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AIcdValueConstraints;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Exercises multi-source diagnostics, absolute paths, line numbers and documentation parity. */
public final class AItcCanonicalConflictDiagnosticsTest {
    private static AIcdCanonicalDefinition AIcDefinition(Path aSource, AInDefinitionSourceKind aKind,
            String aDescription, AInDataTypeKind aType) {
        return new AIcdCanonicalDefinition("urn:test", 1, "test", aKind, aSource.toString(), "Same root documentation", AIcdDataType.object(List.of(new AIcdPropertyDefinition("Value", AIcSourceDataType.fromSourceHints(aType, null, null, AIcdValueConstraints.empty(), AIcdValueConstraints.empty()), ((true) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, aDescription, "Value", null))), List.of(), "Test");
    }

    /** A true self-publication $schema is JSON/YAML metadata, not a missing XML field. */
    @Test
    public void AIcFormatSpecificSchemaUriDoesNotMaskOtherConstants() throws Exception {
        Path locRoot = Files.createTempDirectory("algites-canonical-self-schema-");
        Path locYaml = locRoot.resolve("src/product/yamldefs/demo/test_1.yamldef.schema.json");
        Path locJson = locRoot.resolve("src/product/jsondefs/demo/test_1.jsondef.schema.json");
        Path locXml = locRoot.resolve("src/product/xmldefs/demo/test_1.xsd");
        var locYamlSchema = new AIcdPropertyDefinition("$schema", AIcSourceDataType.fromSourceHints(AInDataTypeKind.STRING, null, null, new AIcdValueConstraints("string", null, null,
                false, false, null, null, null,
                List.of("https://defs.dev.algites.eu/api/yamldefs/demo/test_1.yamldef.schema.json")), AIcdValueConstraints.empty()), ((false) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, "Source schema URL", "Schema", null);
        var locJsonSchema = new AIcdPropertyDefinition("$schema", AIcSourceDataType.fromSourceHints(AInDataTypeKind.STRING, null, null, new AIcdValueConstraints("string", null, null,
                false, false, null, null, null,
                List.of("https://defs.dev.algites.eu/api/jsondefs/demo/test_1.jsondef.schema.json")), AIcdValueConstraints.empty()), ((false) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, "Source schema URL", "Schema", null);
        var locYamlDef = new AIcdCanonicalDefinition("urn:test", 1, "test", AInDefinitionSourceKind.YAMLDEFS, locYaml.toString(), "Doc", AIcdDataType.object(List.of(locYamlSchema)), List.of(), "Test");
        var locJsonDef = new AIcdCanonicalDefinition("urn:test", 1, "test", AInDefinitionSourceKind.JSONDEFS, locJson.toString(), "Doc", AIcdDataType.object(List.of(locJsonSchema)), List.of(), "Test");
        var locXmlDef = new AIcdCanonicalDefinition("urn:test", 1, "test", AInDefinitionSourceKind.XMLDEFS, locXml.toString(), "Doc", AIcdDataType.object(List.of()), List.of(), "Test");
        var locMerged = AIcCanonicalDefinitionMerger.AIcMergeStrict(
                List.of(locYamlDef, locJsonDef, locXmlDef), locRoot);
        Assert.assertTrue(locMerged.dataType().properties().get(0).dataType().constraints().enumValues().isEmpty(),
                "Format-specific $schema URI must not leak into the merged canonical contract");
        Assert.assertEquals(locYamlDef.dataType().properties().get(0).dataType().constraints().enumValues(),
                List.of("https://defs.dev.algites.eu/api/yamldefs/demo/test_1.yamldef.schema.json"),
                "The original YAML publication URI must remain unchanged");
        var locForeign = new AIcdPropertyDefinition("$schema", AIcSourceDataType.fromSourceHints(AInDataTypeKind.STRING, null, null, new AIcdValueConstraints("string", null, null,
                false, false, null, null, null, List.of("https://unrelated.test/schema")), AIcdValueConstraints.empty()), ((false) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, "Source schema URL", "Schema", null);
        String locMessage = Assert.expectThrows(IllegalArgumentException.class,
                () -> AIcCanonicalDefinitionMerger.AIcMergeStrict(List.of(locYamlDef,
                        new AIcdCanonicalDefinition("urn:test", 1, "test", AInDefinitionSourceKind.JSONDEFS, locJson.toString(), "Doc", AIcdDataType.object(List.of(locForeign)), List.of(), "Test"),
                        locXmlDef), locRoot)).getMessage();
        Assert.assertTrue(locMessage.contains("enumValues"), locMessage);
    }

    /** Equivalent JSON/YAML $refs point to the same canonical type despite different file names. */
    @Test
    public void AIcCanonicalReferenceTargetParity() {
        var locJsonReference = new AIcdDefinitionReference("../values/child_1.jsondef.schema.json", 1,
                "child", AIcdDataType.atom(AInDataTypeKind.OBJECT, null));
        var locYamlReference = new AIcdDefinitionReference("../values/child_1.yamldef.schema.json", 1,
                "child", AIcdDataType.atom(AInDataTypeKind.OBJECT, null));
        var locJson = new AIcdCanonicalDefinition("urn:test", 1, "root", AInDefinitionSourceKind.JSONDEFS, "jsondefs/root_1.jsondef.schema.json", null, AIcdDataType.object(List.of(new AIcdPropertyDefinition("Child", AIcSourceDataType.fromSourceHints(AInDataTypeKind.REFERENCE, null, locJsonReference, AIcdValueConstraints.empty(), AIcdValueConstraints.empty()), ((true) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, null, null, null))), List.of(), null);
        var locYaml = new AIcdCanonicalDefinition("urn:test", 1, "root", AInDefinitionSourceKind.YAMLDEFS, "yamldefs/root_1.yamldef.schema.json", null, AIcdDataType.object(List.of(new AIcdPropertyDefinition("Child", AIcSourceDataType.fromSourceHints(AInDataTypeKind.REFERENCE, null, locYamlReference, AIcdValueConstraints.empty(), AIcdValueConstraints.empty()), ((true) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, null, null, null))), List.of(), null);
        AIcCanonicalDefinitionMerger.AIcMergeStrict(List.of(locJson, locYaml), Path.of("."));
        var locWrong = new AIcdDefinitionReference("../values/child_2.yamldef.schema.json", 2,
                "child", AIcdDataType.atom(AInDataTypeKind.OBJECT, null));
        var locChanged = new AIcdCanonicalDefinition("urn:test", 1, "root", AInDefinitionSourceKind.YAMLDEFS, "yamldefs/root_1.yamldef.schema.json", null, AIcdDataType.object(List.of(new AIcdPropertyDefinition("Child", AIcSourceDataType.fromSourceHints(AInDataTypeKind.REFERENCE, null, locWrong, AIcdValueConstraints.empty(), AIcdValueConstraints.empty()), ((true) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, null, null, null))), List.of(), null);
        String locError = Assert.expectThrows(IllegalArgumentException.class,
                () -> AIcCanonicalDefinitionMerger.AIcMergeStrict(List.of(locJson, locChanged), Path.of("."))).getMessage();
        Assert.assertTrue(locError.contains("field 'Child'.dataType.reference"), locError);
    }

    /** Both altered field documentation and changed field types identify the exact sources. */
    @Test
    public void AIcSourcePathsAndPairwiseDocumentationDiff() throws Exception {
        Path locRoot = Files.createTempDirectory("algites-canonical-conflict-");
        Path locYaml = locRoot.resolve("src/product/yamldefs/demo/test_1.yamldef.schema.json");
        Path locJson = locRoot.resolve("src/product/jsondefs/demo/test_1.jsondef.schema.json");
        Path locXml = locRoot.resolve("src/product/xmldefs/demo/test_1.xsd");
        Files.createDirectories(locYaml.getParent());
        Files.createDirectories(locJson.getParent());
        Files.createDirectories(locXml.getParent());
        Files.writeString(locYaml, "{\n  \"properties\": {\n    \"Value\": {\n      \"description\": \"Expected\"\n    }\n  }\n}\n");
        Files.writeString(locJson, "{\n  \"properties\": {\n    \"Value\": {\n      \"description\": \"Changed!\"\n    }\n  }\n}\n");
        Files.writeString(locXml, "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\">\n"
                + "  <xs:complexType name=\"Test\"><xs:sequence>\n"
                + "    <xs:element name=\"Value\" type=\"xs:string\">\n"
                + "      <xs:annotation><xs:documentation>Expected</xs:documentation></xs:annotation>\n"
                + "    </xs:element></xs:sequence></xs:complexType>\n</xs:schema>\n");
        var locFirst = AIcDefinition(locYaml, AInDefinitionSourceKind.YAMLDEFS, "Expected", AInDataTypeKind.STRING);
        var locSecond = AIcDefinition(locJson, AInDefinitionSourceKind.JSONDEFS, "Changed!", AInDataTypeKind.STRING);
        var locThird = AIcDefinition(locXml, AInDefinitionSourceKind.XMLDEFS, "Expected", AInDataTypeKind.STRING);
        String locMessage = Assert.expectThrows(IllegalArgumentException.class,
                () -> AIcCanonicalDefinitionMerger.AIcMergeStrict(List.of(locFirst, locSecond, locThird), locRoot)).getMessage();
        Assert.assertTrue(locMessage.contains("[1] YAMLDEFS vs [3] XMLDEFS: CONSISTENT"), locMessage);
        Assert.assertTrue(locMessage.contains("[1] YAMLDEFS vs [2] JSONDEFS: INCONSISTENT"), locMessage);
        Assert.assertTrue(locMessage.contains("field 'Value'.description"), locMessage);
        Assert.assertTrue(locMessage.contains(locYaml + ":4"), locMessage);
        Assert.assertTrue(locMessage.contains(locJson + ":4"), locMessage);
        Assert.assertTrue(locMessage.contains(locXml.toString()), locMessage);
        String locChangedType = Assert.expectThrows(IllegalArgumentException.class,
                () -> AIcCanonicalDefinitionMerger.AIcMergeStrict(List.of(locFirst,
                        AIcDefinition(locJson, AInDefinitionSourceKind.JSONDEFS, "Expected", AInDataTypeKind.INTEGER),
                        locThird), locRoot)).getMessage();
        Assert.assertTrue(locChangedType.contains("field 'Value'.dataType.kind"), locChangedType);
    }
}
