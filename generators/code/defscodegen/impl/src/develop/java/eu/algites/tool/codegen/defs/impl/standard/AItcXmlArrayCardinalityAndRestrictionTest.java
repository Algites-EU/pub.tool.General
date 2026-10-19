package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.data.dataobject.AInFieldPresenceKind;
import eu.algites.lib.naming.convention.AIiNameConventionCatalog;
import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AIcdValueConstraints;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.nio.file.Files;
import java.nio.file.Path;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verifies preservation and safe narrowing of XSD element occurrence intervals.
 * This test targets the native Java frontend rather than text produced by the
 * independent Python implementation.
 */
public final class AItcXmlArrayCardinalityAndRestrictionTest {
    /** Ensure that collection bounds belong to the recursive ARRAY node, not its scalar child. */
    @Test
    public void AIcProjectNestedArrayBoundsAndProhibitedElement() throws Exception {
        AIcdCanonicalDefinition locDefinition = load("""
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    targetNamespace="urn:test" version="1">
                  <xs:complexType name="Root"><xs:sequence>
                    <xs:element name="codes" type="xs:string" minOccurs="2" maxOccurs="5"/>
                    <xs:element name="absent" type="xs:string" minOccurs="0" maxOccurs="0"/>
                  </xs:sequence></xs:complexType>
                </xs:schema>
                """, null);
        AIcdPropertyDefinition locCodes = locDefinition.dataType().properties().get(0);
        Assert.assertEquals(locCodes.dataType().kind(), AInDataTypeKind.ARRAY);
        Assert.assertEquals(locCodes.dataType().constraints().minItems(), Integer.valueOf(2));
        Assert.assertEquals(locCodes.dataType().constraints().maxItems(), Integer.valueOf(5));
        Assert.assertEquals(locCodes.dataType().elementType().constraints().dataType(), "string");
        Assert.assertEquals(locDefinition.dataType().properties().get(1).presence(), AInFieldPresenceKind.FORBIDDEN);
    }

    /** A derived flat sequence may tighten repeated element cardinality without changing types. */
    @Test
    public void AIcNarrowSequenceWhileRetainingOrderAndPresence() throws Exception {
        AIcdCanonicalDefinition locDefinition = load(sequenceSchema("xs:string", 2, 4), "Derived");
        var locProperties = locDefinition.dataType().properties();
        Assert.assertEquals(locProperties.get(0).dataType().constraints().minItems(), Integer.valueOf(2));
        Assert.assertEquals(locProperties.get(0).dataType().constraints().maxItems(), Integer.valueOf(4));
        Assert.assertEquals(locProperties.get(1).presence(), AInFieldPresenceKind.FORBIDDEN);
    }

    /** Reject widening and nested scalar type changes, even when both fields are ARRAY. */
    @Test
    public void AIcRejectUnsafeNestedArrayRestriction() throws Exception {
        assertRejected(sequenceSchema("xs:string", 0, 4), "minOccurs");
        assertRejected(sequenceSchema("xs:string", 2, 12), "maxOccurs");
        assertRejected(sequenceSchema("xs:int", 2, 4), "changes field type");
    }

    /** Named local sequence groups must retain each element's QName and cardinality. */
    @Test
    public void AIcResolveLocalNamedSequenceGroup() throws Exception {
        AIcdCanonicalDefinition locDefinition = load("""
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    xmlns:tns="urn:test" targetNamespace="urn:test" version="1">
                  <xs:group name="Details"><xs:sequence>
                    <xs:element name="first" type="xs:string"/>
                    <xs:element name="second" type="xs:int" minOccurs="0" maxOccurs="3"/>
                  </xs:sequence></xs:group>
                  <xs:complexType name="Root"><xs:sequence><xs:group ref="tns:Details"/></xs:sequence></xs:complexType>
                </xs:schema>
                """, null);
        Assert.assertEquals(locDefinition.dataType().properties().size(), 2);
        Assert.assertEquals(locDefinition.dataType().properties().get(0).sourceName(), "first");
        Assert.assertEquals(locDefinition.dataType().properties().get(1).dataType().constraints().maxItems(), Integer.valueOf(3));
    }

    /** Recursive or optional multi-element model groups cannot become unrelated optional fields. */
    @Test
    public void AIcRejectLossyNamedGroupFlattening() throws Exception {
        assertRejectedNamedGroup("""
                <xs:group name="Details"><xs:sequence>
                  <xs:element name="first" type="xs:string"/>
                  <xs:element name="second" type="xs:string"/>
                </xs:sequence></xs:group>
                <xs:complexType name="Root"><xs:sequence>
                  <xs:group ref="tns:Details" minOccurs="0"/>
                </xs:sequence></xs:complexType>
                """, "Optional XSD compositor");
        assertRejectedNamedGroup("""
                <xs:group name="Details"><xs:sequence><xs:group ref="tns:Details"/></xs:sequence></xs:group>
                <xs:complexType name="Root"><xs:sequence><xs:group ref="tns:Details"/></xs:sequence></xs:complexType>
                """, "Circular XSD group");
    }

    /** Expect the supplied invalid local group to fail during XSD normalization. */
    private static void assertRejectedNamedGroup(String aContent, String aExpected) throws Exception {
        String locDocument = """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    xmlns:tns="urn:test" targetNamespace="urn:test" version="1">
                """ + aContent + "</xs:schema>";
        try {
            load(locDocument, null);
            Assert.fail("Expected rejected XSD group");
        } catch (IOException locExpected) {
            Assert.assertTrue(locExpected.getMessage().contains(aExpected), locExpected.getMessage());
        }
    }

    /** A named local attribute group provides individually qualified attribute declarations. */
    @Test
    public void AIcResolveAndGuardLocalAttributeGroups() throws Exception {
        var locValid = load("""
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    xmlns:tns="urn:test" targetNamespace="urn:test" version="1">
                  <xs:attributeGroup name="Meta"><xs:attribute name="revision" type="xs:int" use="required"/></xs:attributeGroup>
                  <xs:complexType name="Root"><xs:attributeGroup ref="tns:Meta"/></xs:complexType>
                </xs:schema>
                """, null);
        Assert.assertEquals(locValid.dataType().properties().get(0).sourceName(), "revision");
        Assert.assertEquals(locValid.dataType().properties().get(0).presence(), AInFieldPresenceKind.REQUIRED);
        assertRejectedNamedGroup("""
                <xs:attributeGroup name="Loop"><xs:attributeGroup ref="tns:Loop"/></xs:attributeGroup>
                <xs:complexType name="Root"><xs:attributeGroup ref="tns:Loop"/></xs:complexType>
                """, "Circular XSD attributeGroup");
    }

    /** Cross-format comparison must inspect nested array leaves, not only ARRAY roots. */
    @Test
    public void AIcDetectCrossFormatNestedArrayShapeConflict() {
        var locXml = canonicalArray(AInDefinitionSourceKind.XMLDEFS, AInDataTypeKind.STRING);
        var locJson = canonicalArray(AInDefinitionSourceKind.JSONDEFS, AInDataTypeKind.INTEGER);
        try {
            AIcCanonicalDefinitionMerger.AIcValidate(java.util.List.of(locXml, locJson),
                    false, Path.of(".").toAbsolutePath());
            Assert.fail("Expected incompatible nested array member");
        } catch (IllegalArgumentException locExpected) {
            Assert.assertTrue(locExpected.getMessage().contains(".items.items.kind"), locExpected.getMessage());
        }
    }

    /** Build an otherwise identical two-level array shape for canonical comparison. */
    private static AIcdCanonicalDefinition canonicalArray(AInDefinitionSourceKind aKind,
            AInDataTypeKind aScalar) {
        var locProperty = new AIcdPropertyDefinition("values",
                AIcdDataType.array(AIcdDataType.array(AIcdDataType.atom(aScalar, null))),
                AInFieldPresenceKind.REQUIRED, false, null, null, null);
        return new AIcdCanonicalDefinition("urn:example", 1, "example", aKind,
                aKind.name() + ".schema", null, AIcdDataType.object(java.util.List.of(locProperty)),
                java.util.List.of(), null);
    }

    /** Local global-element references keep their global QName and choice alternatives. */
    @Test
    public void AIcResolveGlobalElementReferencesAndChoice() throws Exception {
        String locXml = """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    xmlns:tns="urn:test" targetNamespace="urn:test" version="1"
                    elementFormDefault="unqualified">
                  <xs:element name="Global" type="xs:string" nillable="true"/>
                  <xs:element name="Another" type="xs:int"/>
                  <xs:complexType name="Root"><xs:sequence>
                    <xs:element ref="tns:Global" maxOccurs="4"/>
                  </xs:sequence></xs:complexType>
                  <xs:complexType name="Select"><xs:choice>
                    <xs:element ref="tns:Global"/>
                    <xs:element ref="tns:Another"/>
                  </xs:choice></xs:complexType>
                </xs:schema>
                """;
        var locObject = load(locXml, "Root");
        var locField = locObject.dataType().properties().get(0);
        Assert.assertEquals(locField.xmlField().namespace(), "urn:test");
        Assert.assertEquals(locField.sourceName(), "Global");
        Assert.assertEquals(locField.dataType().constraints().maxItems(), Integer.valueOf(4));
        Assert.assertTrue(locField.nullable());
        var locChoice = load(locXml, "Select");
        Assert.assertEquals(locChoice.dataType().kind(), AInDataTypeKind.ONE_OF);
        Assert.assertEquals(locChoice.dataType().alternatives().size(), 2);
        Assert.assertEquals(locChoice.dataType().alternatives().get(1).properties().get(0).sourceName(), "Another");
    }

    /** Invalid array intervals are rejected by the shared immutable API. */
    @Test
    public void AIcRejectInvalidCanonicalArrayBounds() {
        try {
            AIcdDataType.array(AIcdDataType.atom(AInDataTypeKind.STRING, null), 3, 2);
            Assert.fail("Expected interval rejection");
        } catch (IllegalArgumentException locExpected) {
            Assert.assertTrue(locExpected.getMessage().contains("minItems"));
        }
    }

    /**
     * Generate two named types in one XSD to test restriction of a flat element sequence.
     *
     * @param aType retained or incorrectly changed scalar XML type
     * @param aMinimum restricted lower occurrence bound
     * @param aMaximum restricted upper occurrence bound
     * @return UTF-8 XML Schema source
     */
    private static String sequenceSchema(String aType, int aMinimum, int aMaximum) {
        return """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    xmlns:tns="urn:test" targetNamespace="urn:test" version="1">
                  <xs:complexType name="Base"><xs:sequence>
                    <xs:element name="entries" type="xs:string" minOccurs="1" maxOccurs="10"/>
                    <xs:element name="optional" type="xs:string" minOccurs="0"/>
                  </xs:sequence></xs:complexType>
                  <xs:complexType name="Derived"><xs:complexContent>
                    <xs:restriction base="tns:Base"><xs:sequence>
                      <xs:element name="entries" type="%s" minOccurs="%d" maxOccurs="%d"/>
                    </xs:sequence></xs:restriction>
                  </xs:complexContent></xs:complexType>
                </xs:schema>
                """.formatted(aType, aMinimum, aMaximum);
    }

    /** Require a diagnostic for an impossible XSD restriction instead of losing type information. */
    private static void assertRejected(String aXml, String aMessage) throws Exception {
        try {
            load(aXml, "Derived");
            Assert.fail("Expected rejected XSD restriction");
        } catch (IOException locExpected) {
            Assert.assertTrue(locExpected.getMessage().contains(aMessage), locExpected.getMessage());
        }
    }

    /**
     * Load a temporary schema with an inert naming catalog. QName and restriction
     * normalization do not depend on naming templates.
     */
    private static AIcdCanonicalDefinition load(String aXml, String aType) throws Exception {
        Path locDirectory = Files.createTempDirectory("algites-cardinality-");
        Path locFile = locDirectory.resolve("cardinality_1.xsd");
        try {
            Files.writeString(locFile, aXml);
            AIiNameConventionCatalog locProfile = (AIiNameConventionCatalog) Proxy.newProxyInstance(
                    AIiNameConventionCatalog.class.getClassLoader(),
                    new Class<?>[] { AIiNameConventionCatalog.class }, (aProxy, aMethod, aArgs) -> null);
            var locRequest = new AIcdDefinitionLoadRequest(locFile, AInDefinitionSourceKind.XMLDEFS, locProfile);
            var locFrontend = new AIcXmlDefsFrontend();
            return aType == null ? locFrontend.load(locRequest) : locFrontend.loadNamedType(locRequest, aType);
        } finally {
            Files.deleteIfExists(locFile);
            Files.deleteIfExists(locDirectory);
        }
    }
}
