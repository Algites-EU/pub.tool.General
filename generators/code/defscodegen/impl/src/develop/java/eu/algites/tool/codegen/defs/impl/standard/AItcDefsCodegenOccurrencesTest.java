package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.bootstrap.model.*;
import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElement;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalList;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1;
import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Native Java equivalents of the Python canonical occurrence regression cases. */
public final class AItcDefsCodegenOccurrencesTest {
    /**
     * Supplies a minimal naming profile for schemas without synthetic members.
     * @return resolved naming profile
     */
    private static AIcCodegenNamingProfileResolver.Profile profile() {
        return new AIcCodegenNamingProfileResolver.Profile("test",
                Map.of("standard_getter", "unused", "standard_setter", "unused"),
                Map.of(), Map.of(), Map.of(), 1, Map.of());
    }

    /** Required fields, optional fields and array bounds survive validation and linking. */
    @Test
    public void AIcRequiredAndArrayBoundsArePreservedAcrossJsonAndYaml() {
        Map<String, Object> schema = Map.of("type", "object", "required", List.of("items"),
                "properties", Map.of("items", Map.of("type", "array", "minItems", 2,
                        "maxItems", 5, "items", Map.of("type", "string")),
                        "nickname", Map.of("type", "string")));
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            var pipeline = new AIcDefsCodegenCanonicalPipeline(profile(), payload -> {
                Assert.assertTrue(payload.containsKey("types"));
            });
            var result = pipeline.process(List.of(
                    new AIcdDefsCodegenSourceDocument(kind, "person.json", schema)));
            var group = (AIcDefsCanonicalElementList) result.types().get(0).structure();
            for (var child : group.children()) {
                var field = (AIcDefsCanonicalElement) child;
                if (field.name().equals("items")) {
                    Assert.assertEquals(field.minItemCount(), 1);
                    var items = (AIcDefsCanonicalList) field.structure();
                    Assert.assertEquals(items.minItemCount(), 2);
                    Assert.assertEquals(items.maxItemCount(), 5);
                } else if (field.name().equals("nickname")) {
                    Assert.assertEquals(field.minItemCount(), 0);
                    Assert.assertEquals(field.maxItemCount(), 1);
                } else Assert.fail("Unexpected member: " + field.name());
            }
        }
    }

    /** XSD element, list and choice group occurrences are retained exactly. */
    @Test
    public void AIcXmlOccurrenceBoundsSurviveNormalization() {
        String xml = """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
                  <xs:complexType name="Person"><xs:sequence>
                    <xs:element name="Name" type="xs:string" minOccurs="0"/>
                    <xs:element name="Tags" type="xs:string" minOccurs="2" maxOccurs="unbounded"/>
                    <xs:choice minOccurs="0" maxOccurs="3">
                      <xs:element name="Yes" type="xs:string"/>
                    </xs:choice>
                  </xs:sequence></xs:complexType>
                </xs:schema>
                """;
        var result = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(
                List.of(new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.XMLDEFS,
                        "person.xsd", xml)));
        var group = (AIcDefsCanonicalElementList) result.types().get(0).structure();
        var name = (AIcDefsCanonicalElement) group.children().get(0);
        var tags = (AIcDefsCanonicalList) group.children().get(1);
        var choice = (AIcDefsCanonicalElementList) group.children().get(2);
        Assert.assertEquals(name.minItemCount(), 0);
        Assert.assertEquals(tags.minItemCount(), 2);
        Assert.assertEquals(tags.maxItemCount(), -1);
        Assert.assertEquals(choice.minItemCount(), 0);
        Assert.assertEquals(choice.maxItemCount(), 3);
    }

    /** Rejects disagreements instead of silently taking one representation's required status. */
    @Test
    public void AIcRequiredPropertyConflictIsReported() {
        var fields = Map.of("name", Map.of("type", "string"));
        var required = Map.of("$id", "urn:example", "type", "object",
                "properties", fields, "required", List.of("name"));
        var optional = Map.of("$id", "urn:example", "type", "object", "properties", fields);
        boolean rejected = false;
        try {
            new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(List.of(
                    new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.JSONDEFS,
                            "required.json", required),
                    new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.YAMLDEFS,
                            "optional.yaml", optional)));
        } catch (IllegalArgumentException expected) {
            rejected = expected.getMessage().contains("Conflicting canonical definitions");
        }
        Assert.assertTrue(rejected);
    }

    /** Reject anyOf because multiple simultaneous matches are not a closed choice. */
    @Test
    public void AIcAnyOfIsNotRewrittenAsExclusiveChoice() {
        boolean rejected = false;
        try {
            new AIcDefsCodegenCanonicalSchemaFrontend(profile()).loadJsonOrYaml(
                    Map.of("anyOf", List.of(Map.of("type", "string"), Map.of("type", "integer"))),
                    "choice.json", AIngSourceInputKind_1.JSONDEFS);
        } catch (UnsupportedOperationException expected) {
            rejected = expected.getMessage().contains("anyOf");
        }
        Assert.assertTrue(rejected);
    }
}
