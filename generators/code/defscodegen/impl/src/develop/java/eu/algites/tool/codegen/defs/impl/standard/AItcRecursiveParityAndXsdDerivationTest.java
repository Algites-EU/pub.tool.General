package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.data.dataobject.AInFieldPresenceKind;
import eu.algites.lib.naming.convention.profile.algites.AIcAlgitesNamingProfiles;
import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIcdValueConstraints;
import eu.algites.tool.codegen.defs.AIcdDefinitionLoadRequest;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Regression tests for canonical recursive parity and restricted XSD derivation. */
public final class AItcRecursiveParityAndXsdDerivationTest {
    /** Deep changes invisible to the old ARRAY/ARRAY projection must be rejected. */
    @Test
    public void AIcRejectNestedLeafTypeMismatch() {
        AIcdDataType locLeft = AIcdDataType.array(AIcdDataType.array(
                AIcdDataType.atom(AInDataTypeKind.INTEGER, null)));
        AIcdDataType locRight = AIcdDataType.array(AIcdDataType.array(
                AIcdDataType.atom(AInDataTypeKind.STRING, null)));
        AIcdCanonicalDefinition locJson = definition(AInDefinitionSourceKind.JSONDEFS, locLeft);
        AIcdCanonicalDefinition locYaml = definition(AInDefinitionSourceKind.YAMLDEFS, locRight);
        try {
            AIcCanonicalDefinitionMerger.AIcValidate(List.of(locJson, locYaml), false, Path.of("."));
            Assert.fail("Distinct nested leaves must not be merged");
        } catch (IllegalArgumentException locExpected) {
            Assert.assertTrue(locExpected.getMessage().contains("items.kind"), locExpected.getMessage());
        }
        AIcCanonicalDefinitionMerger.AIcValidate(List.of(locJson, definition(AInDefinitionSourceKind.YAMLDEFS, locLeft)),
                false, Path.of("."));
    }

    /** Keep all array dimensions in Java and Python signatures without flattening nested scalars. */
    @Test
    public void AIcRenderNestedArrayDimensions() {
        AIcdDataType locGrid = AIcdDataType.array(AIcdDataType.array(
                AIcdDataType.atom(AInDataTypeKind.INTEGER, null)));
        Assert.assertEquals(AIcScalarGeneration.recursiveArrayType(locGrid, true),
                "java.util.List<java.util.List<java.math.BigInteger>>");
        Assert.assertEquals(AIcScalarGeneration.recursiveArrayType(locGrid, false),
                "tuple[tuple[int, ...], ...]");
        AIcdDataType locNestedChoice = AIcdDataType.array(AIcdDataType.array(
                AIcdDataType.choice(AInDataTypeKind.ONE_OF, List.of(
                        AIcdDataType.atom(AInDataTypeKind.STRING, null),
                        AIcdDataType.atom(AInDataTypeKind.INTEGER, null)))));
        try {
            AIcScalarGeneration.recursiveArrayType(locNestedChoice, true);
            Assert.fail("Nested choices require explicit generated named contracts");
        } catch (IllegalArgumentException locExpected) {
            Assert.assertTrue(locExpected.getMessage().contains("named contract"));
        }
    }

    /**
     * Ensures nested object and choice array contracts preserve all dimensions and
     * produce covariant Java read-only collections for future type refinement.
     * Unlike scalar array projections, each generated contract array dimension
     * must use {@code ? extends} so specialized getters can override ancestors.
     */
    @Test
    public void AIcRenderNestedNamedContracts() {
        AIcdDataType locInline = AIcdDataType.array(AIcdDataType.array(
                AIcdDataType.object(List.of(new AIcdPropertyDefinition("code", AIcSourceDataType.fromSourceHints(AInDataTypeKind.STRING, null, null, AIcdValueConstraints.empty(), AIcdValueConstraints.empty()), ((true) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, null, null, null)))));
        var locField = new AIcdPropertyDefinition("lines", locInline, ((false) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, null, null, null);
        var locModel = new AIcdCanonicalDefinition("urn:example:invoice", 1, "invoice", AInDefinitionSourceKind.JSONDEFS, "invoice_1.jsondef.schema.json", null, AIcdDataType.object(List.of(locField)), List.of(), null);
        var locRequest = new eu.algites.tool.codegen.defs.AIcdCodeGenerationRequest(locModel,
                eu.algites.tool.codegen.defs.AInCodeGenerationTarget.JAVA, "example.invoice",
                AItcConfiguredNamingProfiles.javaProfile());
        Assert.assertEquals(AIcRecursiveContractType.render(locField, locRequest,
                new AIcGenerationNames(), true, new java.util.TreeSet<>()),
                "java.util.List<? extends java.util.List<? extends AIigInvoiceLinesItemsItems_1>>");
        AIcdDataType locChoice = AIcdDataType.array(AIcdDataType.choice(
                AInDataTypeKind.ONE_OF, List.of(
                        AIcdDataType.atom(AInDataTypeKind.INTEGER, null),
                        AIcdDataType.atom(AInDataTypeKind.STRING, null))));
        var locChoiceField = new AIcdPropertyDefinition("selection", locChoice, ((false) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, null, null, null);
        Assert.assertEquals(AIcRecursiveContractType.render(locChoiceField, locRequest,
                new AIcGenerationNames(), true, new java.util.TreeSet<>()),
                "java.util.List<? extends AIigInvoiceSelectionItems_1>");
    }

    /** A permitted same-schema attribute restriction must project prohibited use. */
    @Test
    public void AIcProjectAttributeRestriction() throws Exception {
        Path locDir = Files.createTempDirectory("algites-xsd-restriction-");
        Path locSource = locDir.resolve("derived_1.xsd");
        try {
            Files.writeString(locSource, """
                    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                      xmlns:tns="urn:derivation" targetNamespace="urn:derivation" version="1">
                      <xs:complexType name="Base">
                        <xs:attribute name="code" type="xs:string" use="optional"/>
                      </xs:complexType>
                      <xs:complexType name="Derived"><xs:complexContent>
                        <xs:restriction base="tns:Base">
                          <xs:attribute name="code" type="xs:string" use="prohibited"/>
                        </xs:restriction>
                      </xs:complexContent></xs:complexType>
                      <xs:element name="root" type="tns:Derived"/>
                    </xs:schema>
                    """);
            var locModel = new AIcXmlDefsFrontend().load(AItcConfiguredNamingProfiles.load(locSource,
                    AInDefinitionSourceKind.XMLDEFS, AItcConfiguredNamingProfiles.javaProfile()));
            Assert.assertEquals(locModel.dataType().properties().size(), 1);
            Assert.assertEquals(locModel.dataType().properties().get(0).presence(), AInFieldPresenceKind.FORBIDDEN);
        } finally {
            Files.deleteIfExists(locSource);
            Files.deleteIfExists(locDir);
        }
    }

    /** Retain the same top-level field projection when testing nested data-type changes. */
    private static AIcdCanonicalDefinition definition(AInDefinitionSourceKind aKind, AIcdDataType aDataType) {
        var locField = new AIcdPropertyDefinition("items", aDataType, ((false) ? eu.algites.lib.data.dataobject.AInFieldPresenceKind.REQUIRED : eu.algites.lib.data.dataobject.AInFieldPresenceKind.ALLOWED), false, null, null, null);
        return new AIcdCanonicalDefinition("urn:example:root", 1, "root", aKind, "root", null, AIcdDataType.object(List.of(locField)), List.of(), null);
    }
}
