package eu.algites.tool.codegen.defs;

import eu.algites.lib.naming.convention.AIcAlgitesNamingProfiles;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import javax.tools.ToolProvider;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Regression coverage for shared YAML/JSON types and local schema references. */
public final class AItcCanonicalRepresentationsTest {
    private AIcdCanonicalDefinition AIcLoad(String aFile, AInDefinitionSourceKind aKind) throws Exception {
        Path locPath = Path.of(getClass().getClassLoader().getResource(aFile).toURI());
        return new AIcDefaultDefsCodegenService().load(new AIcdDefinitionLoadRequest(
                locPath, aKind, AIcAlgitesNamingProfiles.javaProfile()));
    }

    /** Confirms that wire-compatible representations merge while retaining both descriptions and origins. */
    @Test
    public void AIcCommonMetadataRepresentations() throws Exception {
        AIcdCanonicalDefinition locYaml = AIcLoad("document-common-metadata_1.yamldef.schema.json", AInDefinitionSourceKind.YAMLDEFS);
        AIcdCanonicalDefinition locJson = AIcLoad("document-common-metadata_1.jsondef.schema.json", AInDefinitionSourceKind.JSONDEFS);
        Assert.assertEquals(locYaml.properties(), locJson.properties());
        Assert.assertNotEquals(locYaml.identity(), locJson.identity());
        AIcdCanonicalDefinition locMerged = AIcCanonicalDefinitionMerger.AIcMerge(List.of(locYaml, locJson));
        Assert.assertTrue(locMerged.description().contains(locYaml.description()));
        Assert.assertTrue(locMerged.description().contains(locJson.description()));
        for (AInCodeGenerationTarget locTarget : AInCodeGenerationTarget.values()) {
            var locProfile = locTarget == AInCodeGenerationTarget.JAVA
                    ? AIcAlgitesNamingProfiles.javaProfile() : AIcAlgitesNamingProfiles.pythonProfile();
            AIcdGeneratedSource locSource = new AIcDefaultDefsCodegenService().generate(new AIcdCodeGenerationRequest(
                    locMerged, locTarget, "example.generated", locProfile));
            Assert.assertTrue(locSource.source().contains(locYaml.identity()));
            Assert.assertTrue(locSource.source().contains(locJson.identity()));
            Assert.assertTrue(locSource.source().contains("Optional absolute URI of the schema describing this root document."));
            if (locTarget == AInCodeGenerationTarget.PYTHON) {
                Path locRoot = Files.createTempDirectory("defs-generated-python-");
                Path locFile = locRoot.resolve("generated.py");
                Files.writeString(locFile, locSource.source());
                var locProcess = new ProcessBuilder("python3", "-c",
                        "import runpy; ns=runpy.run_path(" + "'" + locFile + "'" + "); cls=next(v for v in ns.values() if isinstance(v,type) and hasattr(v,'from_mapping')); assert cls.from_mapping({'$schema':'https://example.test/schema'}).to_mapping()=={'$schema':'https://example.test/schema'}")
                        .inheritIO().start();
                Assert.assertEquals(locProcess.waitFor(), 0);
            }
            if (locTarget == AInCodeGenerationTarget.JAVA) {
                Path locRoot = Files.createTempDirectory("defs-generated-compile-");
                Path locFile = locRoot.resolve(locSource.relativePath());
                Files.createDirectories(locFile.getParent());
                Files.writeString(locFile, locSource.source());
                Assert.assertEquals(ToolProvider.getSystemJavaCompiler().run(null, null, null,
                        "-d", locRoot.toString(), locFile.toString()), 0);
            }
        }
        AIcdPropertyDefinition locChanged = new AIcdPropertyDefinition("$schema", AInValueKind.INTEGER, false, false, null, null, "Different type");
        AIcdCanonicalDefinition locIncompatible = new AIcdCanonicalDefinition(locJson.identity(), locJson.version(),
                locJson.logicalName(), locJson.kind(), locJson.sourceKind(), locJson.sourceResource(),
                locJson.description(), List.of(locChanged), List.of());
        Assert.expectThrows(IllegalArgumentException.class,
                () -> AIcCanonicalDefinitionMerger.AIcMerge(List.of(locYaml, locIncompatible)));
    }

    /** Resolves local pointers and anchors without inventing a file name or definition version. */
    @Test
    public void AIcLocalSchemaReferences() throws Exception {
        Path locPath = Files.createTempDirectory("defs-local-references-").resolve("local_1.jsondef.schema.json");
        Files.writeString(locPath, """
                {"type":"object", "$defs":{"text":{"type":"string","description":"Inline text"},
                  "list":{"$anchor":"Items","type":"array","items":{"type":"integer"}},
                  "alias":{"$ref":"#/$defs/text"}},
                 "properties":{"text":{"$ref":"#/$defs/alias"},"items":{"$ref":"#Items"}}}
                """);
        AIcdCanonicalDefinition locDefinition = new AIcDefaultDefsCodegenService().load(new AIcdDefinitionLoadRequest(
                locPath, AInDefinitionSourceKind.JSONDEFS, AIcAlgitesNamingProfiles.javaProfile()));
        Assert.assertEquals(locDefinition.properties().get(0).valueKind(), AInValueKind.STRING);
        Assert.assertEquals(locDefinition.properties().get(0).description(), "Inline text");
        Assert.assertEquals(locDefinition.properties().get(1).valueKind(), AInValueKind.ARRAY);
        Assert.assertEquals(locDefinition.properties().get(1).itemValueKind(), AInValueKind.INTEGER);
        Files.writeString(locPath, "{\"type\":\"object\",\"properties\":{\"bad\":{\"$ref\":\"#/$defs/missing\"}}}");
        Assert.expectThrows(IllegalArgumentException.class, () -> new AIcDefaultDefsCodegenService().load(
                new AIcdDefinitionLoadRequest(locPath, AInDefinitionSourceKind.JSONDEFS, AIcAlgitesNamingProfiles.javaProfile())));
    }
    /** Keeps composed object fields and filename identity for XML schemas with generic type names. */
    @Test
    public void AIcComposedAndXmlContracts() throws Exception {
        Path locRoot = Files.createTempDirectory("defs-composition-");
        Path locJson = locRoot.resolve("composed_1.jsondef.schema.json");
        Files.writeString(locJson, """
                {"$defs":{"content":{"type":"object","properties":{"Name":{"type":"string"}},"required":["Name"]}},
                 "allOf":[{"$ref":"#/$defs/content"}]}
                """);
        var locService = new AIcDefaultDefsCodegenService();
        var locProfile = AIcAlgitesNamingProfiles.javaProfile();
        var locDefinition = locService.load(new AIcdDefinitionLoadRequest(locJson, AInDefinitionSourceKind.JSONDEFS, locProfile));
        Assert.assertEquals(locDefinition.kind(), AInDefinitionKind.OBJECT);
        Assert.assertEquals(locDefinition.properties().size(), 1);
        Assert.assertTrue(locDefinition.properties().get(0).required());
        Path locXml = locRoot.resolve("xml-contract_1.xsd");
        Files.writeString(locXml, """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
                  <xs:complexType name="Configuration"><xs:sequence>
                    <xs:element name="Item" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
                  </xs:sequence></xs:complexType>
                </xs:schema>
                """);
        locDefinition = locService.load(new AIcdDefinitionLoadRequest(locXml, AInDefinitionSourceKind.XMLDEFS, locProfile));
        Assert.assertEquals(locDefinition.logicalName(), "xml-contract");
        Assert.assertEquals(locDefinition.properties().get(0).valueKind(), AInValueKind.ARRAY);
        Assert.assertEquals(locDefinition.properties().get(0).itemValueKind(), AInValueKind.STRING);
    }

}
