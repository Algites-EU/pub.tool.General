package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenElement;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenElementList;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenList;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenXmlWireName;
import eu.algites.tool.codegen.defs.AInDefsCodegenXmlValueKind;
import eu.algites.tool.codegen.defs.AInDefsCodegenSourceInputKind;
import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Checks exact XML QName fidelity in the native Java canonical frontend,
 * linker, merger and generated-schema payload. Java and Python frontends
 * must agree even when XML field names are lexically identical but in
 * different namespace/attribute contexts.
 */
public final class AItcDefsCodegenCanonicalXmlWireNameTest {
    /**
     * Controlled profile for a fixture without synthetic type-name generation.
     * @return minimal naming context
     */
    private static AIcCodegenNamingProfileResolver.Profile profile() {
        return new AIcCodegenNamingProfileResolver.Profile("test", Map.of(), Map.of(),
                Map.of(), Map.of(), 1, Map.of());
    }

    /**
     * Parses elements and attributes using both form defaults and explicit overrides.
     * Verifies the same metadata survives normalization, merging and JSON projection.
     */
    @Test
    public void AIcCanonicalXmlWireNamesSurviveLinkingAndProjection() {
        String xsd = """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    targetNamespace="urn:doc" elementFormDefault="qualified"
                    attributeFormDefault="unqualified">
                  <xs:complexType name="Doc"><xs:sequence>
                    <xs:element name="Name" type="xs:string"/>
                    <xs:element name="Line" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
                    <xs:element name="Unqualified" type="xs:integer" form="unqualified"/>
                  </xs:sequence>
                  <xs:attribute name="code" type="xs:string" use="required"/>
                  <xs:attribute name="flag" type="xs:boolean" form="qualified"/>
                  </xs:complexType>
                </xs:schema>
                """;
        var processor = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> {});
        var declaration = processor.process(List.of(new AIcdDefsCodegenSourceDocument(
                AInDefsCodegenSourceInputKind.XMLDEFS, "doc.xsd", xsd))).types().get(0);
        var fields = ((AIcdDefsCodegenElementList) declaration.structure()).children();
        Assert.assertEquals(fields.size(), 5);
        Assert.assertEquals(((AIcdDefsCodegenElement) fields.get(0)).xmlWire(),
                new AIcdDefsCodegenXmlWireName("urn:doc", "Name", AInDefsCodegenXmlValueKind.ELEMENT));
        Assert.assertEquals(((AIcdDefsCodegenList) fields.get(1)).xmlWire(),
                new AIcdDefsCodegenXmlWireName("urn:doc", "Line", AInDefsCodegenXmlValueKind.ELEMENT));
        Assert.assertEquals(((AIcdDefsCodegenElement) fields.get(2)).xmlWire(),
                new AIcdDefsCodegenXmlWireName("", "Unqualified", AInDefsCodegenXmlValueKind.ELEMENT));
        Assert.assertEquals(((AIcdDefsCodegenElement) fields.get(3)).xmlWire(),
                new AIcdDefsCodegenXmlWireName("", "code", AInDefsCodegenXmlValueKind.ATTRIBUTE));
        Assert.assertEquals(((AIcdDefsCodegenElement) fields.get(4)).xmlWire(),
                new AIcdDefsCodegenXmlWireName("urn:doc", "flag", AInDefsCodegenXmlValueKind.ATTRIBUTE));
        var merged = AIcDefsCodegenCanonicalModelMerger.merge(List.of(declaration, declaration));
        var again = ((AIcdDefsCodegenElementList) merged.get(0).structure()).children();
        Assert.assertEquals(((AIcdDefsCodegenElement) again.get(3)).xmlWire(),
                ((AIcdDefsCodegenElement) fields.get(3)).xmlWire());
        var payload = AIcDefsCodegenCanonicalContractPayload.emit(merged).toString();
        Assert.assertTrue(payload.contains("xml_wire"));
        Assert.assertTrue(payload.contains("ATTRIBUTE"));
        Assert.assertTrue(payload.contains("namespace_uri=urn:doc"));
    }

    /**
     * Prevents merging two distinct XML expanded names or representation kinds.
     */
    /**
     * Invalid schema-wide form defaults must be rejected even if the XSD has no
     * fields whose declarations would otherwise cause QName resolution.
     */
    @Test
    public void AIcCanonicalXmlWireInvalidFormDefaultsAreRejected() {
        var frontend = new AIcDefsCodegenCanonicalSchemaFrontend(profile());
        for (String attribute : List.of("elementFormDefault", "attributeFormDefault")) {
            String xsd = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" "
                    + attribute + "=\"invalid\">"
                    + "<xs:complexType name=\"Empty\"/>"
                    + "</xs:schema>";
            boolean rejected = false;
            try {
                frontend.loadXsd(xsd, "invalid.xsd");
            } catch (IllegalArgumentException expected) {
                rejected = expected.getMessage().contains("form default");
            }
            Assert.assertTrue(rejected);
        }
    }

    @Test
    public void AIcCanonicalXmlWireConflictsAreRejected() {
        var scalar = new eu.algites.tool.codegen.defs.AIcdDefsCodegenScalar(
                eu.algites.tool.codegen.defs.AInDefsCodegenScalarKind.STRING, "");
        var left = new AIcdDefsCodegenElement("code", scalar, List.of(), Map.of(),
                0, 1, "", new AIcdDefsCodegenXmlWireName("", "code", AInDefsCodegenXmlValueKind.ATTRIBUTE));
        var right = new AIcdDefsCodegenElement("code", scalar, List.of(), Map.of(),
                0, 1, "", new AIcdDefsCodegenXmlWireName("urn:doc", "code", AInDefsCodegenXmlValueKind.ATTRIBUTE));
        var typeA = new eu.algites.tool.codegen.defs.AIcdDefsCodegenType("urn:Doc", "Doc",
                eu.algites.tool.codegen.defs.AInDefsCodegenTypeOrigin.DECLARED, List.of("Doc"), List.of(),
                new AIcdDefsCodegenElementList(
                        eu.algites.tool.codegen.defs.AInDefsCodegenComposition.SEQUENCE, List.of(left)),
                eu.algites.tool.codegen.defs.AInDefsCodegenResolutionState.RESOLVED, Map.of());
        var typeB = new eu.algites.tool.codegen.defs.AIcdDefsCodegenType("urn:Doc", "Doc",
                eu.algites.tool.codegen.defs.AInDefsCodegenTypeOrigin.DECLARED, List.of("Doc"), List.of(),
                new AIcdDefsCodegenElementList(
                        eu.algites.tool.codegen.defs.AInDefsCodegenComposition.SEQUENCE, List.of(right)),
                eu.algites.tool.codegen.defs.AInDefsCodegenResolutionState.RESOLVED, Map.of());
        boolean rejected = false;
        try {
            AIcDefsCodegenCanonicalModelMerger.merge(List.of(typeA, typeB));
        } catch (IllegalArgumentException expected) {
            rejected = expected.getMessage().contains("XML QName");
        }
        Assert.assertTrue(rejected);
    }
}
