package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Set;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verifies actual cross-document XSD complexContent extension resolution and
 * rejection of particles whose occurrence semantics cannot be projected safely.
 */
public final class AItcXmlImportedInheritanceTest {
    /**
     * Resolves a locally imported base declaration without changing its wire
     * namespace, so generated contracts can inherit the correct base type.
     *
     * @throws Exception if the test schema files cannot be created or parsed
     */
    @Test
    public void AIcResolveImportedExtensionBase() throws Exception {
        Path locDirectory = Files.createTempDirectory("algites-xsd-import-");
        Path locBase = locDirectory.resolve("base_1.xsd");
        Path locDerived = locDirectory.resolve("derived_1.xsd");
        try {
            Files.writeString(locBase, """
                    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                      targetNamespace="urn:base" elementFormDefault="qualified" version="1">
                      <xs:complexType name="Base"><xs:sequence>
                        <xs:element name="amount" type="xs:int"/>
                      </xs:sequence></xs:complexType>
                    </xs:schema>
                    """);
            Files.writeString(locDerived, """
                    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                      xmlns:b="urn:base" targetNamespace="urn:derived"
                      elementFormDefault="qualified" version="1">
                      <xs:import namespace="urn:base" schemaLocation="base_1.xsd"/>
                      <xs:complexType name="Derived"><xs:complexContent>
                        <xs:extension base="b:Base"><xs:sequence>
                          <xs:element name="code" type="xs:string"/>
                        </xs:sequence></xs:extension>
                      </xs:complexContent></xs:complexType>
                    </xs:schema>
                    """);
            var locRequest = new AIcdDefinitionLoadRequest(
                    locDerived, AInDefinitionSourceKind.XMLDEFS, naming());
            var locFrontend = new AIcXmlDefsFrontend();
            Assert.assertEquals(locFrontend.rootExtensionBaseQName(locRequest), "{urn:base}Base");
            var locFields = locFrontend.load(locRequest).dataType().properties();
            Assert.assertEquals(locFields.size(), 2);
            Assert.assertEquals(locFields.get(0).xmlField().namespace(), "urn:base");
            Assert.assertEquals(locFields.get(1).xmlField().namespace(), "urn:derived");
        } finally {
            Files.deleteIfExists(locDerived);
            Files.deleteIfExists(locBase);
            Files.deleteIfExists(locDirectory);
        }
    }

    /**
     * Ensures that a repeated group is rejected instead of being flattened into
     * unrelated element arrays, which would misrepresent its semantics.
     *
     * @throws Exception if the test schema cannot be created or parsed
     */
    @Test
    public void AIcRejectRepeatedSequence() throws Exception {
        Path locSchema = Files.createTempFile("algites-group-", "_1.xsd");
        try {
            Files.writeString(locSchema, """
                    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" version="1">
                      <xs:complexType name="Repeated"><xs:sequence maxOccurs="2">
                        <xs:element name="code" type="xs:string"/>
                      </xs:sequence></xs:complexType>
                    </xs:schema>
                    """);
            try {
                new AIcXmlDefsFrontend().load(new AIcdDefinitionLoadRequest(
                        locSchema, AInDefinitionSourceKind.XMLDEFS, naming()));
                throw new AssertionError("Repeated group must be rejected");
            } catch (java.io.IOException locExpected) {
                Assert.assertTrue(locExpected.getMessage().contains("compositor"));
            }
        } finally {
            Files.deleteIfExists(locSchema);
        }
    }

    /**
     * Reads an auxiliary named type as a separate canonical declaration, without
     * changing the existing file-based primary definition.
     *
     * @throws Exception if test source creation or schema parsing fails
     */
    @Test
    public void AIcDiscoverAndLoadAdditionalNamedTypes() throws Exception {
        Path locSource = Files.createTempFile("algites-multitype-", "_1.xsd");
        try {
            Files.writeString(locSource, """
                    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                      xmlns:t="urn:multi" targetNamespace="urn:multi" version="1">
                      <xs:complexType name="BaseType">
                        <xs:attribute name="id" type="xs:string"/>
                      </xs:complexType>
                      <xs:complexType name="DerivedType"><xs:complexContent>
                        <xs:extension base="t:BaseType">
                          <xs:attribute name="child" type="xs:string"/>
                        </xs:extension>
                      </xs:complexContent></xs:complexType>
                      <xs:element name="root" type="t:DerivedType"/>
                    </xs:schema>
                    """);
            var locFrontend = new AIcXmlDefsFrontend();
            var locRequest = new AIcdDefinitionLoadRequest(
                    locSource, AInDefinitionSourceKind.XMLDEFS, naming());
            Assert.assertEquals(locFrontend.additionalNamedTypeNames(locSource), java.util.List.of("BaseType"));
            var locBase = locFrontend.loadNamedType(locRequest, "BaseType");
            Assert.assertEquals(locBase.logicalName(), "base-type");
            Assert.assertEquals(locBase.dataType().properties().size(), 1);
            Assert.assertEquals(locFrontend.schemaNamespace(locRequest), "urn:multi");
            Assert.assertEquals(locFrontend.rootExtensionBaseQName(locRequest), "{urn:multi}BaseType");
            Assert.assertEquals(locFrontend.namedTypeExtensionBaseQName(locRequest, "BaseType"), null);
        } finally {
            Files.deleteIfExists(locSource);
        }
    }

    /**
     * Provides a deterministic naming test double for XML frontend tests, with
     * no dependency on installed YAML catalogs or external build plugins.
     *
     * @return a naming catalog sufficient for source-name normalization
     */
    private static AIiNameConventionCatalog naming() {
        return new AIiNameConventionCatalog() {
            /** Returns the supported versioned Java interface convention. */
            @Override public Set<String> names() { return Set.of("algites-java-gen-intf-versioned"); }
            /** Formats a simple deterministic identifier for generated tests. */
            @Override public String format(String aProfile, String aStructure,
                    Map<String, String> aValues, String aSourceIdentifierConvention) {
                return "AIig" + aValues.getOrDefault("identifier", "Type") + "_1";
            }
            /** Returns no reverse-parsed names in this isolated test. */
            @Override public Map<String, String> parse(String aProfile, String aStructure, String aValue) {
                return Map.of();
            }
            /** Accepts deterministic source identifiers used by the test. */
            @Override public boolean matches(String aProfile, String aStructure, String aValue) { return true; }
        };
    }
}
