package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.model.*;
import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElement;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalXmlWireName;
import eu.algites.tool.codegen.defs.model.AIngXmlWireNameValueKind_1;
import eu.algites.tool.codegen.defs.model.AIngSourceInputKind_1;
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
                AIngSourceInputKind_1.XMLDEFS, "doc.xsd", xsd))).types().get(0);
        var fields = ((AIcDefsCanonicalElementList) declaration.structure()).children();
        Assert.assertEquals(fields.size(), 5);
        Assert.assertEquals(((AIcDefsCanonicalElement) fields.get(0)).xmlWire(),
                new AIcDefsCanonicalXmlWireName("urn:doc", "Name", AIngXmlWireNameValueKind_1.ELEMENT));
        Assert.assertEquals(((AIcDefsCanonicalList) fields.get(1)).xmlWire(),
                new AIcDefsCanonicalXmlWireName("urn:doc", "Line", AIngXmlWireNameValueKind_1.ELEMENT));
        Assert.assertEquals(((AIcDefsCanonicalElement) fields.get(2)).xmlWire(),
                new AIcDefsCanonicalXmlWireName("", "Unqualified", AIngXmlWireNameValueKind_1.ELEMENT));
        Assert.assertEquals(((AIcDefsCanonicalElement) fields.get(3)).xmlWire(),
                new AIcDefsCanonicalXmlWireName("", "code", AIngXmlWireNameValueKind_1.ATTRIBUTE));
        Assert.assertEquals(((AIcDefsCanonicalElement) fields.get(4)).xmlWire(),
                new AIcDefsCanonicalXmlWireName("urn:doc", "flag", AIngXmlWireNameValueKind_1.ATTRIBUTE));
        var merged = AIcDefsCodegenCanonicalModelMerger.merge(List.of(declaration, declaration));
        var again = ((AIcDefsCanonicalElementList) merged.get(0).structure()).children();
        Assert.assertEquals(((AIcDefsCanonicalElement) again.get(3)).xmlWire(),
                ((AIcDefsCanonicalElement) fields.get(3)).xmlWire());
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
        var scalar = new eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalScalar(
                eu.algites.tool.codegen.defs.model.AIngScalarKind_1.STRING, "");
        var left = new AIcDefsCanonicalElement("code", scalar, List.of(), Map.of(),
                0, 1, "", new AIcDefsCanonicalXmlWireName("", "code", AIngXmlWireNameValueKind_1.ATTRIBUTE));
        var right = new AIcDefsCanonicalElement("code", scalar, List.of(), Map.of(),
                0, 1, "", new AIcDefsCanonicalXmlWireName("urn:doc", "code", AIngXmlWireNameValueKind_1.ATTRIBUTE));
        var typeA = new eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType("urn:Doc", "Doc",
                eu.algites.tool.codegen.defs.model.AIngTypeOrigin_1.DECLARED, List.of("Doc"), List.of(),
                new AIcDefsCanonicalElementList(
                        eu.algites.tool.codegen.defs.model.AIngComposition_1.SEQUENCE, List.of(left)),
                eu.algites.tool.codegen.defs.model.AIngResolutionState_1.RESOLVED, Map.of());
        var typeB = new eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType("urn:Doc", "Doc",
                eu.algites.tool.codegen.defs.model.AIngTypeOrigin_1.DECLARED, List.of("Doc"), List.of(),
                new AIcDefsCanonicalElementList(
                        eu.algites.tool.codegen.defs.model.AIngComposition_1.SEQUENCE, List.of(right)),
                eu.algites.tool.codegen.defs.model.AIngResolutionState_1.RESOLVED, Map.of());
        boolean rejected = false;
        try {
            AIcDefsCodegenCanonicalModelMerger.merge(List.of(typeA, typeB));
        } catch (IllegalArgumentException expected) {
            rejected = expected.getMessage().contains("XML QName");
        }
        Assert.assertTrue(rejected);
    }
}
