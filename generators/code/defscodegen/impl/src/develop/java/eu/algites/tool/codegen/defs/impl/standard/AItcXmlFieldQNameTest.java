package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.data.dataobject.xmldefs.AInXmlValueKind;
import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AIcdXmlFieldRepresentation;
import eu.algites.tool.codegen.defs.AInCodeGenerationTarget;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Set;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Ensures native Java XML Schema projection retains element/attribute QName semantics,
 * matching the Python frontend without inferring qualified names from Java identifiers.
 */
public final class AItcXmlFieldQNameTest {
    /**
     * Verifies local XSD qualification overrides and generator annotations.
     *
     * @throws Exception if temporary source creation or XSD parsing fails
     */
    @Test
    public void AIcLocalXmlMemberQNameAndWireKind() throws Exception {
        Path locSource = Files.createTempFile("algites-xml-qname-", "_1.xsd");
        try {
            Files.writeString(locSource, schema("unqualified", "unqualified"));
            var locFrontend = new AIcXmlDefsFrontend();
            var locRequest = new AIcdDefinitionLoadRequest(locSource,
                    AInDefinitionSourceKind.XMLDEFS, naming());
            var locDefinition = locFrontend.load(locRequest);
            Map<String, AIcdXmlFieldRepresentation> locFields = new java.util.LinkedHashMap<>();
            for (var locField : locDefinition.dataType().properties()) locFields.put(locField.sourceName(), locField.xmlField());
            Assert.assertEquals(locFields.get("amount"), new AIcdXmlFieldRepresentation(
                    "urn:ledger", "amount", AInXmlValueKind.ELEMENT, 1, 1));
            Assert.assertEquals(locFields.get("note"), new AIcdXmlFieldRepresentation(
                    "", "note", AInXmlValueKind.ELEMENT, 1, 1));
            Assert.assertEquals(locFields.get("currency"), new AIcdXmlFieldRepresentation(
                    "", "currency", AInXmlValueKind.ATTRIBUTE, 0, 1));
            Assert.assertEquals(locFields.get("ref"), new AIcdXmlFieldRepresentation(
                    "urn:ledger", "ref", AInXmlValueKind.ATTRIBUTE, 0, 1));
            var locGenerated = new AIcSchemaContractInterfaceGenerator().generate(
                    new AIcdCodeGenerationRequest(locDefinition, AInCodeGenerationTarget.JAVA,
                            "example.ledger", new AIcSelectedNamingCatalog(naming(), Map.of(
                                    eu.algites.tool.codegen.defs.AInDefsNameRole.INTERFACE_TYPE,
                                    "algites-java-gen-intf-versioned_1",
                                    eu.algites.tool.codegen.defs.AInDefsNameRole.INTERFACE_TYPE_FILE_STEM,
                                    "algites-java-gen-intf-versioned_1")), locFrontend.rootTypeQName(locRequest)));
            Assert.assertTrue(locGenerated.source().contains("AIaXmlDataObjectField("));
            Assert.assertTrue(locGenerated.source().contains("AInXmlValueKind.ATTRIBUTE"));
            Assert.assertTrue(locGenerated.source().contains("namespaceLocalName = \"amount\""));
        } finally {
            Files.deleteIfExists(locSource);
        }
    }

    /**
     * Checks that qualified schema defaults are applied only when not overridden.
     *
     * @throws Exception if an XSD cannot be read
     */
    @Test
    public void AIcAttributeFormDefaultAndInvalidForm() throws Exception {
        Path locSource = Files.createTempFile("algites-xml-form-", "_1.xsd");
        try {
            Files.writeString(locSource, schema("qualified", "unqualified"));
            var locRequest = new AIcdDefinitionLoadRequest(locSource,
                    AInDefinitionSourceKind.XMLDEFS, naming());
            var locFields = new AIcXmlDefsFrontend().load(locRequest).dataType().properties();
            Assert.assertEquals(locFields.stream().filter(aField -> "currency".equals(aField.sourceName()))
                    .findFirst().orElseThrow().xmlField().namespace(), "urn:ledger");
            Files.writeString(locSource, schema("qualified", "invalid"));
            try {
                new AIcXmlDefsFrontend().load(locRequest);
                throw new AssertionError("Invalid local form must not be silently normalized");
            } catch (java.io.IOException locExpected) {
                Assert.assertTrue(locExpected.getMessage().contains("form"));
            }
        } finally {
            Files.deleteIfExists(locSource);
        }
    }

    /**
     * Verifies that type-less prohibited attributes cannot silently switch their
     * inherited expanded QName before a scalar type is copied from the base.
     *
     * @throws Exception if temporary XSD setup fails
     */
    @Test
    public void AIcRejectQNameDriftOnProhibitedAttribute() throws Exception {
        Path locSource = Files.createTempFile("algites-xml-restriction-", "_1.xsd");
        try {
            String locXml = """
                    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                      xmlns:tns="urn:ledger" targetNamespace="urn:ledger" version="1">
                      <xs:complexType name="Base">
                        <xs:attribute name="code" type="xs:string" form="qualified"/>
                      </xs:complexType>
                      <xs:complexType name="Restricted"><xs:complexContent>
                        <xs:restriction base="tns:Base"><xs:attribute name="code" use="prohibited"/>
                        </xs:restriction>
                      </xs:complexContent></xs:complexType>
                      <xs:element name="root" type="tns:Restricted"/>
                    </xs:schema>
                    """;
            Files.writeString(locSource, locXml);
            var locRequest = new AIcdDefinitionLoadRequest(locSource,
                    AInDefinitionSourceKind.XMLDEFS, naming());
            try {
                new AIcXmlDefsFrontend().load(locRequest);
                throw new AssertionError("Conflicting XML QName must be rejected");
            } catch (java.io.IOException locExpected) {
                Assert.assertTrue(locExpected.getMessage().contains("QName"));
            }
            Files.writeString(locSource, locXml.replace("name=\"code\" use=\"prohibited\"",
                    "name=\"code\" use=\"prohibited\" form=\"qualified\""));
            var locField = new AIcXmlDefsFrontend().load(locRequest).dataType().properties().get(0);
            Assert.assertEquals(locField.xmlField().namespace(), "urn:ledger");
        } finally {
            Files.deleteIfExists(locSource);
        }
    }

    private static String schema(String aAttributeDefault, String aNoteForm) {
        return """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="urn:ledger"
                   elementFormDefault="qualified" attributeFormDefault="%s" version="1">
                   <xs:complexType name="LedgerType"><xs:sequence>
                     <xs:element name="amount" type="xs:decimal"/>
                     <xs:element name="note" type="xs:string" form="%s"/>
                   </xs:sequence>
                   <xs:attribute name="currency" type="xs:string"/>
                   <xs:attribute name="ref" type="xs:string" form="qualified"/>
                   </xs:complexType>
                </xs:schema>
                """.formatted(aAttributeDefault, aNoteForm);
    }

    private static AIiNameConventionCatalog naming() {
        return new AIiNameConventionCatalog() {
            /** Minimal naming profile is sufficient for deterministic QName tests. */
            @Override public Set<String> names() { return Set.of("algites-java-gen-intf-versioned_1"); }
            /** Formats the source logical identifier into a Java-compatible test name. */
            @Override public String format(String aProfile, String aStructure,
                    Map<String, String> aVariables, String aLexical) {
                String locName = aVariables.getOrDefault("identifier", "Ledger");
                return switch (aStructure) {
                    case "main_container_name", "file_name_stem" -> "AIig" + locName.replace("_", "") + "_1";
                    case "field_name" -> "get" + locName;
                    case "constant_name" -> locName.toUpperCase(java.util.Locale.ROOT);
                    default -> locName;
                };
            }
            /** These tests do not need reverse-format interpretation. */
            @Override public Map<String, String> parse(String aProfile, String aStructure, String aValue) {
                return Map.of();
            }
            /** Every test filename is intentionally treated as compatible. */
            @Override public boolean matches(String aProfile, String aStructure, String aValue) {
                return true;
            }
        };
    }
}
