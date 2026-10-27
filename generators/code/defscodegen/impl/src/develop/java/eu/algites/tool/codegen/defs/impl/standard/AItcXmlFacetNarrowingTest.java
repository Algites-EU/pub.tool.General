package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.naming.convention.profile.algites.AIcAlgitesNamingProfiles;
import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.nio.file.Files;
import java.nio.file.Path;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Regression tests for monotonic XSD facets and safe attribute restrictions. */
public final class AItcXmlFacetNarrowingTest {
    /** A derived numeric type may narrow both bounds without losing their exclusivity. */
    @Test
    public void AIcProjectStrictNumericBounds() throws Exception {
        AIcdCanonicalDefinition locDefinition = simpleType(
                "<xs:minInclusive value=\"10\"/><xs:maxExclusive value=\"200\"/>",
                "<xs:minExclusive value=\"10\"/><xs:maxInclusive value=\"100\"/>", "xs:decimal");
        var locConstraints = locDefinition.dataType().properties().get(0).dataType().constraints();
        Assert.assertEquals(locConstraints.minimum(), "10");
        Assert.assertTrue(locConstraints.exclusiveMinimum());
        Assert.assertEquals(locConstraints.maximum(), "100");
        Assert.assertFalse(locConstraints.exclusiveMaximum());
    }

    /** Reject inherited numeric and string restrictions that would be silently loosened. */
    @Test
    public void AIcRejectRelaxedScalarFacets() throws Exception {
        assertRejected("<xs:minInclusive value=\"10\"/>", "<xs:minInclusive value=\"9\"/>",
                "xs:decimal", "minimum");
        assertRejected("<xs:maxExclusive value=\"10\"/>", "<xs:maxInclusive value=\"10\"/>",
                "xs:decimal", "maximum");
        assertRejected("<xs:minLength value=\"3\"/>", "<xs:minLength value=\"2\"/>",
                "xs:string", "minLength");
        assertRejected("<xs:pattern value=\"[A-Z]+\"/>", "<xs:pattern value=\"[A-Z]{3}\"/>",
                "xs:string", "inherited XSD pattern");
        assertRejected("<xs:minInclusive value=\"10\"/>", "<xs:totalDigits value=\"5\"/>",
                "xs:decimal", "Unsupported XSD restriction facet");
    }

    /** Explicit enum values must remain a subset of those permitted by the base type. */
    @Test
    public void AIcRejectWidenedEnumerations() throws Exception {
        var locDefinition = simpleType("<xs:enumeration value=\"A\"/><xs:enumeration value=\"B\"/>",
                "<xs:enumeration value=\"B\"/>", "xs:string");
        Assert.assertEquals(locDefinition.dataType().properties().get(0).dataType().constraints().enumValues(), java.util.List.of("B"));
        assertRejected("<xs:enumeration value=\"A\"/><xs:enumeration value=\"B\"/>",
                "<xs:enumeration value=\"C\"/>", "xs:string", "enumeration");
    }

    /** Restricting an attribute to plain string must not drop inherited length constraints. */
    @Test
    public void AIcRejectAttributeFacetRelaxation() throws Exception {
        String locXml = """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                  xmlns:tns="urn:facets" targetNamespace="urn:facets" version="1">
                  <xs:simpleType name="Code"><xs:restriction base="xs:string">
                    <xs:minLength value="3"/>
                  </xs:restriction></xs:simpleType>
                  <xs:complexType name="Base"><xs:attribute name="code" type="tns:Code"/></xs:complexType>
                  <xs:complexType name="Derived"><xs:complexContent><xs:restriction base="tns:Base">
                    <xs:attribute name="code" type="xs:string"/>
                  </xs:restriction></xs:complexContent></xs:complexType>
                  <xs:element name="root" type="tns:Derived"/>
                </xs:schema>
                """;
        assertRejectedXml(locXml, "minLength");
    }

    /** A prohibited attribute may omit its type and must retain its base constraints. */
    @Test
    public void AIcInheritProhibitedAttributeType() throws Exception {
        String locXml = """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                  xmlns:tns="urn:facets" targetNamespace="urn:facets" version="1">
                  <xs:simpleType name="Code"><xs:restriction base="xs:string">
                    <xs:minLength value="3"/>
                  </xs:restriction></xs:simpleType>
                  <xs:complexType name="Base"><xs:attribute name="code" type="tns:Code"/></xs:complexType>
                  <xs:complexType name="Derived"><xs:complexContent><xs:restriction base="tns:Base">
                    <xs:attribute name="code" use="prohibited"/>
                  </xs:restriction></xs:complexContent></xs:complexType>
                  <xs:element name="root" type="tns:Derived"/>
                </xs:schema>
                """;
        var locField = loadXml(locXml).dataType().properties().get(0);
        Assert.assertEquals(locField.presence(), eu.algites.lib.data.dataobject.AInFieldPresenceKind.FORBIDDEN);
        Assert.assertEquals(locField.dataType().constraints().minLength(), Integer.valueOf(3));
    }

    /** Builds the same pair of named restricted types used by the Python regression suite. */
    private static AIcdCanonicalDefinition simpleType(String aBase, String aDerived, String aBuiltin)
            throws Exception {
        String locXml = """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                  xmlns:tns="urn:facets" targetNamespace="urn:facets" version="1">
                """ + "<xs:simpleType name=\"Base\"><xs:restriction base=\"" + aBuiltin + "\">"
                + aBase + "</xs:restriction></xs:simpleType>"
                + "<xs:simpleType name=\"Derived\"><xs:restriction base=\"tns:Base\">"
                + aDerived + "</xs:restriction></xs:simpleType>"
                + "<xs:complexType name=\"Container\"><xs:attribute name=\"code\" type=\"tns:Derived\"/>"
                + "</xs:complexType><xs:element name=\"root\" type=\"tns:Container\"/></xs:schema>";
        return loadXml(locXml);
    }

    /** Confirms that invalid or unsupported facets fail rather than producing relaxed contracts. */
    private static void assertRejected(String aBase, String aDerived, String aBuiltin, String aExpected)
            throws Exception {
        try {
            simpleType(aBase, aDerived, aBuiltin);
            throw new AssertionError("Expected XSD restriction rejection: " + aExpected);
        } catch (java.io.IOException locExpected) {
            Assert.assertTrue(locExpected.getMessage().contains(aExpected));
        }
    }

    /** Parses a temporary XSD and removes it after materializing the canonical definition. */
    private static AIcdCanonicalDefinition loadXml(String aXml) throws Exception {
        Path locSource = Files.createTempFile("algites-facets_1-", ".xsd");
        try {
            Files.writeString(locSource, aXml);
            return new AIcXmlDefsFrontend().load(new AIcdDefinitionLoadRequest(locSource,
                    AInDefinitionSourceKind.XMLDEFS, AIcAlgitesNamingProfiles.javaProfile()));
        } finally {
            Files.deleteIfExists(locSource);
        }
    }

    /** Reuses the common reader to assert that an XSD fails safely. */
    private static void assertRejectedXml(String aXml, String aExpected) throws Exception {
        try {
            loadXml(aXml);
            throw new AssertionError("Expected XSD restriction rejection: " + aExpected);
        } catch (java.io.IOException locExpected) {
            Assert.assertTrue(locExpected.getMessage().contains(aExpected));
        }
    }
}
