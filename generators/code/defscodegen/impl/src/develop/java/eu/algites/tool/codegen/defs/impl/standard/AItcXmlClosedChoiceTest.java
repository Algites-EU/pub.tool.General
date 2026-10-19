package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AInCodeGenerationTarget;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Set;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Checks that the native Java XSD frontend and code generator preserve XML
 * branch QNames in a finite choice, rather than flattening choice particles.
 */
public final class AItcXmlClosedChoiceTest {
    /**
     * Reads a mandatory XML choice, generates its type and the two branch
     * contracts, and checks the technology marker and XML metadata.
     *
     * @throws Exception if a temporary schema cannot be created or parsed
     */
    @Test
    public void AIcGenerateXmlChoiceContracts() throws Exception {
        Path locSchema = Files.createTempFile("algites-choice-", "_1.xsd");
        try {
            Files.writeString(locSchema, """
                    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                      targetNamespace="urn:test:choice" elementFormDefault="qualified" version="1">
                      <xs:complexType name="OptionType"><xs:choice>
                        <xs:element name="text" type="xs:string"/>
                        <xs:element name="amount" type="xs:integer"/>
                      </xs:choice></xs:complexType>
                    </xs:schema>
                    """);
            AIiNameConventionCatalog locNaming = naming();
            AIcdDefinitionLoadRequest locLoad = new AIcdDefinitionLoadRequest(
                    locSchema, AInDefinitionSourceKind.XMLDEFS, locNaming);
            AIcXmlDefsFrontend locFrontend = new AIcXmlDefsFrontend();
            var locDefinition = locFrontend.load(locLoad);
            Assert.assertEquals(locDefinition.dataType().kind(), AInDataTypeKind.ONE_OF);
            Assert.assertEquals(locDefinition.dataType().alternatives().size(), 2);
            Assert.assertEquals(locDefinition.dataType().alternatives().get(0)
                    .properties().get(0).xmlField().namespace(), "urn:test:choice");
            var locRequest = new AIcdCodeGenerationRequest(locDefinition, AInCodeGenerationTarget.JAVA,
                    "example.choice", locNaming, locFrontend.rootTypeQName(locLoad));
            var locSources = new AIcClosedChoiceGenerator().generate(locRequest);
            Assert.assertEquals(locSources.size(), 5);
            Assert.assertTrue(locSources.get(0).source().contains("sealed interface"));
            Assert.assertTrue(locSources.get(0).source().contains("AIiXmlDataObject"));
            Assert.assertTrue(locSources.get(0).source().contains("namespaceLocalName = \"OptionType\""));
            Assert.assertTrue(locSources.get(1).source().contains("AIaXmlDataObjectField"));
            Assert.assertTrue(locSources.get(3).source().contains("record "));
        } finally {
            Files.deleteIfExists(locSchema);
        }
    }

    /**
     * Tests require only deterministic output names, not the full YAML naming
     * catalog; production generation uses the configured catalog instead.
     */
    private static AIiNameConventionCatalog naming() {
        return new AIiNameConventionCatalog() {
            /** Supported source and output conventions. */
            @Override public Set<String> names() { return Set.of("algites-java-gen-intf-versioned"); }
            /** Produces a stable name from the nominal identifier. */
            @Override public String format(String aProfile, String aStructure,
                    Map<String, String> aVariables, String aLexical) {
                String locId = aVariables.getOrDefault("identifier", "Unknown");
                String locName = locId.replaceAll("[^A-Za-z0-9]", "");
                return switch (aStructure) {
                    case "main_container_name", "file_name_stem" -> "AIig" + locName + "_1";
                    case "field_name" -> "get" + locName;
                    case "constant_name" -> locName.toUpperCase(java.util.Locale.ROOT);
                    default -> locName;
                };
            }
            /** Reverse parsing is not required by this unit test. */
            @Override public Map<String, String> parse(String aProfile, String aStructure,
                    String aValue) { return Map.of(); }
            /** Every test identifier is accepted. */
            @Override public boolean matches(String aProfile, String aStructure, String aValue) { return true; }
        };
    }
}
