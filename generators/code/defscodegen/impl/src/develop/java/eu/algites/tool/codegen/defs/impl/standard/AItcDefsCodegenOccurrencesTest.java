package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenElement;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenElementList;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenList;
import eu.algites.tool.codegen.defs.AInDefsCodegenSourceInputKind;
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
        for (var kind : List.of(AInDefsCodegenSourceInputKind.JSONDEFS,
                AInDefsCodegenSourceInputKind.YAMLDEFS)) {
            var pipeline = new AIcDefsCodegenCanonicalPipeline(profile(), payload -> {
                Assert.assertTrue(payload.containsKey("types"));
            });
            var result = pipeline.process(List.of(
                    new AIcdDefsCodegenSourceDocument(kind, "person.json", schema)));
            var group = (AIcdDefsCodegenElementList) result.types().get(0).structure();
            for (var child : group.children()) {
                var field = (AIcdDefsCodegenElement) child;
                if (field.name().equals("items")) {
                    Assert.assertEquals(field.minOccurs(), 1);
                    var items = (AIcdDefsCodegenList) field.structure();
                    Assert.assertEquals(items.minOccurs(), 2);
                    Assert.assertEquals(items.maxOccurs(), 5);
                } else if (field.name().equals("nickname")) {
                    Assert.assertEquals(field.minOccurs(), 0);
                    Assert.assertEquals(field.maxOccurs(), 1);
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
                List.of(new AIcdDefsCodegenSourceDocument(AInDefsCodegenSourceInputKind.XMLDEFS,
                        "person.xsd", xml)));
        var group = (AIcdDefsCodegenElementList) result.types().get(0).structure();
        var name = (AIcdDefsCodegenElement) group.children().get(0);
        var tags = (AIcdDefsCodegenList) group.children().get(1);
        var choice = (AIcdDefsCodegenElementList) group.children().get(2);
        Assert.assertEquals(name.minOccurs(), 0);
        Assert.assertEquals(tags.minOccurs(), 2);
        Assert.assertEquals(tags.maxOccurs(), -1);
        Assert.assertEquals(choice.minOccurs(), 0);
        Assert.assertEquals(choice.maxOccurs(), 3);
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
                    new AIcdDefsCodegenSourceDocument(AInDefsCodegenSourceInputKind.JSONDEFS,
                            "required.json", required),
                    new AIcdDefsCodegenSourceDocument(AInDefsCodegenSourceInputKind.YAMLDEFS,
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
                    "choice.json", AInDefsCodegenSourceInputKind.JSONDEFS);
        } catch (UnsupportedOperationException expected) {
            rejected = expected.getMessage().contains("anyOf");
        }
        Assert.assertTrue(rejected);
    }
}
