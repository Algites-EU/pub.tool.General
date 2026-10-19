package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.data.dataobject.AInFieldPresenceKind;
import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Set;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Checks that native Java XSD global-declaration lookup traverses only local,
 * namespace-consistent include and import graphs. Referenced XML declarations
 * preserve their owning expanded QName rather than borrowing the referencing
 * schema's namespace.
 */
public final class AItcXmlImportedDeclarationReferencesTest {
    /**
     * Resolves imported global elements, model groups, attribute groups and
     * attributes while retaining their original expanded names and presence.
     *
     * @throws Exception if temporary schemas cannot be written or parsed
     */
    @Test
    public void AIcResolveImportedGlobalDeclarations() throws Exception {
        Path locFolder = Files.createTempDirectory("algites-imported-declarations-");
        try {
            Files.writeString(locFolder.resolve("base_1.xsd"), """
                    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                         xmlns:b="urn:base" targetNamespace="urn:base" version="1"
                         elementFormDefault="qualified">
                      <xs:element name="Document" type="xs:int" nillable="true"/>
                      <xs:group name="Details"><xs:sequence>
                        <xs:element name="Nested" type="xs:string"/>
                      </xs:sequence></xs:group>
                      <xs:attribute name="Token" type="xs:string"/>
                      <xs:attributeGroup name="Keys"><xs:attribute ref="b:Token" use="required"/></xs:attributeGroup>
                    </xs:schema>
                    """);
            Path locDerived = locFolder.resolve("derived_1.xsd");
            Files.writeString(locDerived, """
                    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                        xmlns:b="urn:base" targetNamespace="urn:derived" version="1">
                      <xs:import namespace="urn:base" schemaLocation="base_1.xsd"/>
                      <xs:complexType name="Derived"><xs:sequence>
                        <xs:element ref="b:Document" minOccurs="0" maxOccurs="3"/>
                        <xs:group ref="b:Details"/>
                      </xs:sequence><xs:attributeGroup ref="b:Keys"/></xs:complexType>
                    </xs:schema>
                    """);
            var locFields = new AIcXmlDefsFrontend().load(new AIcdDefinitionLoadRequest(
                    locDerived, AInDefinitionSourceKind.XMLDEFS, naming())).dataType().properties();
            Assert.assertEquals(locFields.size(), 3);
            for (var locField : locFields) Assert.assertEquals(locField.xmlField().namespace(), "urn:base");
            Assert.assertEquals(locFields.get(0).sourceName(), "Document");
            Assert.assertEquals(locFields.get(0).dataType().constraints().maxItems(), Integer.valueOf(3));
            Assert.assertEquals(locFields.get(2).sourceName(), "Token");
            Assert.assertEquals(locFields.get(2).presence(), AInFieldPresenceKind.REQUIRED);
        } finally {
            for (String locName : new String[] {"derived_1.xsd", "base_1.xsd"})
                Files.deleteIfExists(locFolder.resolve(locName));
            Files.deleteIfExists(locFolder);
        }
    }

    /**
     * Rejects incorrect declared namespaces instead of using an imported
     * declaration that happens to have the matching local name.
     *
     * @throws Exception if temporary schemas cannot be written or parsed
     */
    @Test
    public void AIcRejectMismatchedImportedNamespace() throws Exception {
        Path locFolder = Files.createTempDirectory("algites-import-validation-");
        try {
            Files.writeString(locFolder.resolve("base_1.xsd"), """
                    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                        targetNamespace="urn:base" version="1">
                      <xs:element name="Document" type="xs:string"/>
                    </xs:schema>
                    """);
            Path locDerived = locFolder.resolve("derived_1.xsd");
            Files.writeString(locDerived, """
                    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                        xmlns:b="urn:base" targetNamespace="urn:derived" version="1">
                      <xs:import namespace="urn:wrong" schemaLocation="base_1.xsd"/>
                      <xs:complexType name="Derived"><xs:sequence>
                        <xs:element ref="b:Document"/>
                      </xs:sequence></xs:complexType>
                    </xs:schema>
                    """);
            try {
                new AIcXmlDefsFrontend().load(new AIcdDefinitionLoadRequest(
                        locDerived, AInDefinitionSourceKind.XMLDEFS, naming()));
                throw new AssertionError("A mismatched import namespace was accepted");
            } catch (IOException locExpected) {
                Assert.assertEquals(locExpected.getMessage().contains("namespace disagrees"), true);
            }
        } finally {
            for (String locName : new String[] {"derived_1.xsd", "base_1.xsd"})
                Files.deleteIfExists(locFolder.resolve(locName));
            Files.deleteIfExists(locFolder);
        }
    }

    /**
     * Uses a standalone naming test implementation because XSD QName
     * resolution must not require a YAML naming resource to be installed.
     *
     * @return a naming catalog sufficient for isolated frontend tests
     */
    private static AIiNameConventionCatalog naming() {
        return new AIiNameConventionCatalog() {
            /** No naming conventions are queried during this test. */
            @Override public Set<String> names() { return Set.of(); }
            /** Formatting does not participate in XML source loading. */
            @Override public String format(String aProfile, String aStructure,
                    Map<String, String> aValues, String aSourceIdentifierConvention) {
                throw new UnsupportedOperationException();
            }
            /** Reverse parsing does not participate in XML source loading. */
            @Override public Map<String, String> parse(String aProfile, String aStructure, String aName) {
                throw new UnsupportedOperationException();
            }
            /** Naming validation does not participate in XML source loading. */
            @Override public boolean matches(String aProfile, String aStructure, String aName) { return false; }
        };
    }
}
