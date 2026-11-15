package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.model.*;
import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElement;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.model.AIngSourceInputKind_1;
import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verifies metadata and annotations survive canonical parsing, merging, and linking
 * in the Java backend as well as the separate Python backend.
 */
public final class AItcDefsCodegenCanonicalMetadataTest {
    /**
     * Returns the minimum complete naming profile required for scalar fields.
     * @return a valid common naming profile without synthetic naming demands
     */
    private static AIcCodegenNamingProfileResolver.Profile profile() {
        return new AIcCodegenNamingProfileResolver.Profile("test",
                Map.of("standard_getter", "unused", "standard_setter", "unused"),
                Map.of(), Map.of(), Map.of(), 1, Map.of());
    }

    /** Checks that JSON/YAML contract metadata remains available to the emitter. */
    @Test
    public void AIcVersionAndFieldDocumentationRemainVisibleInPayload() {
        Map<String, Object> schema = Map.of("$id", "urn:person", "title", "Person",
                "type", "object", "x-algites-schema-version", "1.3",
                "description", "Person record", "properties", Map.of("name",
                        Map.of("type", "string", "description", "Legal name")));
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            var result = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                    new AIcdDefsCodegenSourceDocument(kind, "person.schema", schema)));
            var type = result.types().get(0);
            Assert.assertEquals(type.schemaVersion(), "1.3");
            Assert.assertEquals(type.description(), "Person record");
            var field = (AIcDefsCanonicalElement) ((AIcDefsCanonicalElementList) type.structure())
                    .children().get(0);
            Assert.assertEquals(field.description(), "Legal name");
            @SuppressWarnings("unchecked")
            Map<String, Object> wire = (Map<String, Object>) ((List<?>) result.payload().get("types")).get(0);
            Assert.assertEquals(wire.get("schema_version"), "1.3");
            Assert.assertEquals(wire.get("description"), "Person record");
        }
    }

    /** Checks XSD documentation is interpreted from annotation/documentation, not ignored. */
    @Test
    public void AIcXmlDocumentationAndVersionRemainVisible() {
        String xml = """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" x-algites-schema-version="2">
                  <xs:complexType name="Person">
                    <xs:annotation><xs:documentation>Person record</xs:documentation></xs:annotation>
                    <xs:sequence><xs:element name="Name" type="xs:string">
                      <xs:annotation><xs:documentation>Legal name</xs:documentation></xs:annotation>
                    </xs:element></xs:sequence>
                  </xs:complexType>
                </xs:schema>
                """;
        var result = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.XMLDEFS, "person.xsd", xml)));
        var type = result.types().get(0);
        Assert.assertEquals(type.schemaVersion(), "2");
        Assert.assertEquals(type.description(), "Person record");
        var field = (AIcDefsCanonicalElement) ((AIcDefsCanonicalElementList) type.structure())
                .children().get(0);
        Assert.assertEquals(field.description(), "Legal name");
    }

    /** Missing version or documentation never overwrites explicit values from another source. */
    @Test
    public void AIcMissingSourceMetadataDoesNotOverrideAnotherSource() {
        var properties = Map.of("name", Map.of("type", "string"));
        var a = Map.<String, Object>of("$id", "urn:person", "title", "Person", "type", "object",
                "properties", properties);
        var b = Map.<String, Object>of("$id", "urn:person", "title", "Person", "type", "object",
                "description", "Person record", "x-algites-schema-version", "4",
                "properties", properties);
        var result = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.JSONDEFS, "a.json", a),
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.YAMLDEFS, "b.yaml", b)));
        Assert.assertEquals(result.types().get(0).schemaVersion(), "4");
        Assert.assertEquals(result.types().get(0).description(), "Person record");
        Assert.assertEquals(result.types().get(0).sourceBindings().size(), 2);
    }
}
