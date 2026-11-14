package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.bootstrap.model.*;
import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElement;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Native Java source-to-canonical pipeline integration with the mandatory generated
 * contract validator callback and no dependency on the old Defs implementation.
 */
public final class AItcDefsCodegenCanonicalPipelineTest {
    /**
     * Supplies a minimal validated naming context for test documents which require
     * no synthetic type or accessor name rendering.
     *
     * @return type-safe profile for scalar and reference-only canonical fixtures
     */
    private static AIcCodegenNamingProfileResolver.Profile profile() {
        return new AIcCodegenNamingProfileResolver.Profile("test",
                Map.of("standard_getter", "unused", "standard_setter", "unused"),
                Map.of(), Map.of(), Map.of(), 1, Map.of());
    }

    /**
     * Constructs two representation families of the same logical JSON Schema model,
     * including a self-recursive named {@code $defs} type and a validating callback.
     */
    @Test
    public void AIcCrossTechnologyRecursivePipelineReturnsValidatedGraph() {
        var definitions = Map.of("Node", Map.of("type", "object", "properties",
                Map.of("next", Map.of("$ref", "#/$defs/Node"))));
        Map<String, Object> schema = Map.of("x-algites-schema-id", "urn:shared",
                "title", "Shared", "type", "object", "properties",
                Map.of("value", Map.of("$ref", "#/$defs/Node")), "$defs", definitions);
        var validationCalls = new AtomicInteger();
        var pipeline = new AIcDefsCodegenCanonicalPipeline(profile(), document -> {
            Assert.assertEquals(((List<?>) document.get("types")).size(), 2);
            validationCalls.incrementAndGet();
        });
        var result = pipeline.process(List.of(
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.JSONDEFS,
                        "source.json", schema),
                new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.YAMLDEFS,
                        "source.yaml", schema)));
        Assert.assertEquals(validationCalls.get(), 1);
        Assert.assertEquals(result.types().size(), 2);
        Assert.assertEquals(result.types().get(1).identity(), "urn:shared#/$defs/Node");
        Assert.assertEquals(result.types().get(1).sourceBindings().size(), 2);
        var members = (AIcDefsCanonicalElementList) result.types().get(1).structure();
        var element = (AIcDefsCanonicalElement) members.children().get(0);
        Assert.assertEquals(((AIcDefsCanonicalType) element.structure()).targetIdentity(),
                "urn:shared#/$defs/Node");
    }

    /**
     * Verifies native XMLDEFS parsing, named recursive TYPE resolution, and the
     * mandatory unnormalized contract validation callback without mock frontends.
     */
    @Test
    public void AIcXsdRecursiveSourceIsLinkedWithoutInfiniteTraversal() {
        var xml = """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
                <xs:complexType name="Node"><xs:sequence>
                  <xs:element name="child" type="Node"/>
                </xs:sequence></xs:complexType></xs:schema>
                """;
        var pipeline = new AIcDefsCodegenCanonicalPipeline(profile(), payload ->
                Assert.assertEquals(((List<?>) payload.get("types")).size(), 1));
        var result = pipeline.process(List.of(new AIcdDefsCodegenSourceDocument(
                AIngSourceInputKind_1.XMLDEFS, "schema.xsd", xml)));
        var group = (AIcDefsCanonicalElementList) result.types().get(0).structure();
        Assert.assertEquals(((AIcDefsCanonicalType)
                ((AIcDefsCanonicalElement) group.children().get(0)).structure()).targetIdentity(), "Node");
    }
    /**
     * Confirms that XMLDEFS namespace-qualified declarations retain independent
     * identities and a derived type points to its exact canonical base identity.
     */
    @Test
    public void AIcNamespacedXsdExtensionRetainsBaseIdentity() {
        String xsd = """
                <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                    xmlns:tns="urn:family" targetNamespace="urn:family">
                  <xs:complexType name="Base"><xs:sequence>
                    <xs:element name="Id" type="xs:string"/>
                  </xs:sequence></xs:complexType>
                  <xs:complexType name="Child"><xs:complexContent>
                    <xs:extension base="tns:Base"><xs:sequence>
                      <xs:element name="Name" type="xs:string"/>
                    </xs:sequence></xs:extension>
                  </xs:complexContent></xs:complexType>
                </xs:schema>
                """;
        var result = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(
                List.of(new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.XMLDEFS,
                        "family.xsd", xsd)));
        Assert.assertEquals(result.types().size(), 2);
        Assert.assertEquals(result.types().get(0).identity(), "{urn:family}Base");
        Assert.assertEquals(result.types().get(1).identity(), "{urn:family}Child");
        Assert.assertEquals(result.types().get(1).inheritedFromTypes(), List.of("{urn:family}Base"));
    }

    /**
     * Ensures that JSONDEFS declarations nested inside {@code $defs} retain
     * their inherited base links, rather than emitting incomplete scalar stubs.
     */
    @Test
    public void AIcNamedJsonDefinitionsResolveInheritance() {
        Map<String, Object> schema = Map.of("x-algites-schema-id", "urn:shared", "$defs", Map.of(
                "Base", Map.of("type", "object", "properties", Map.of("id", Map.of("type", "string"))),
                "Child", Map.of("type", "object", "allOf", List.of(Map.of("$ref", "#/$defs/Base")),
                        "properties", Map.of("value", Map.of("type", "string")))));
        var result = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(
                List.of(new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.JSONDEFS,
                        "models.json", schema)));
        AIcDefsCanonicalType child = result.types().stream().filter(
                item -> item.name().equals("Child")).findFirst().orElseThrow();
        Assert.assertEquals(child.inheritedFromTypes(), List.of("urn:shared#/$defs/Base"));
    }
    /**
     * Ensures malformed or unsupported JSON Schema unions and open property maps
     * cannot silently degrade to a scalar ANY or an incomplete object contract.
     */
    @Test
    public void AIcFrontendRejectsLossyJsonAndYamlSchemas() {
        var frontend = new AIcDefsCodegenCanonicalSchemaFrontend(profile());
        var bad = List.<Map<String, Object>>of(
                Map.of("type", List.of("string", "integer")),
                Map.of("type", List.of("string", "null")),
                Map.of("type", "unknown"),
                Map.of("enum", List.of(1, true)),
                Map.of("type", "string", "enum", List.of("a", 1)),
                Map.of("type", "object", "additionalProperties", true),
                Map.of("type", "array", "items", false),
                Map.of("oneOf", List.of(Map.of("type", "string")),
                        "anyOf", List.of(Map.of("type", "integer"))));
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            for (var schema : bad) {
                boolean rejected = false;
                try {
                    frontend.loadJsonOrYaml(schema, "invalid.schema.json", kind);
                } catch (IllegalArgumentException | UnsupportedOperationException expected) {
                    rejected = true;
                }
                Assert.assertTrue(rejected);
            }
            var array = frontend.loadJsonOrYaml(Map.of("type", "array"), "array.schema.json", kind);
            Assert.assertEquals(array.structure().kind(),
                    eu.algites.tool.codegen.defs.bootstrap.model.AIngStructureKind_1.LIST);
        }
    }

    /**
     * Preserves QName namespace identity when an XMLDEFS local type has the
     * same lexical name as a built-in XSD scalar.
     */
    @Test
    public void AIcXsdQNameBuiltinAndLocalNameCollisionAreDistinct() {
        var xsd = """
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
                     xmlns:tns="urn:test" targetNamespace="urn:test">
              <xs:complexType name="string"><xs:sequence>
                <xs:element name="marker" type="xs:boolean"/>
              </xs:sequence></xs:complexType>
              <xs:complexType name="Holder"><xs:sequence>
                <xs:element name="builtin" type="xs:string"/>
                <xs:element name="user" type="tns:string"/>
              </xs:sequence></xs:complexType>
            </xs:schema>
            """;
        var result = new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(
                List.of(new AIcdDefsCodegenSourceDocument(AIngSourceInputKind_1.XMLDEFS,
                        "types.xsd", xsd)));
        var holder = result.types().stream().filter(item -> item.name().equals("Holder"))
                .findFirst().orElseThrow();
        var members = (AIcDefsCanonicalElementList) holder.structure();
        var builtin = (AIcDefsCanonicalElement) members.children().get(0);
        var named = (AIcDefsCanonicalElement) members.children().get(1);
        Assert.assertEquals(builtin.structure().kind(),
                eu.algites.tool.codegen.defs.bootstrap.model.AIngStructureKind_1.SCALAR);
        Assert.assertEquals(((AIcDefsCanonicalType) named.structure()).targetIdentity(),
                "{urn:test}string");
    }

    /**
     * Rejects undeclared XML namespace prefixes even when the unqualified
     * local name happens to match a type declared in the document.
     */
    @Test
    public void AIcXsdRejectsUndeclaredQNamePrefix() {
        String xsd = """
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
              <xs:complexType name="Node"><xs:sequence>
                <xs:element name="child" type="missing:Node"/>
              </xs:sequence></xs:complexType>
            </xs:schema>
            """;
        boolean rejected = false;
        try {
            new AIcDefsCodegenCanonicalPipeline(profile(), ignored -> { }).process(
                    List.of(new AIcdDefsCodegenSourceDocument(
                            AIngSourceInputKind_1.XMLDEFS, "broken.xsd", xsd)));
        } catch (IllegalArgumentException expected) {
            rejected = true;
        }
        Assert.assertTrue(rejected);
    }

    /**
     * Verifies that integrated JSONDEFS/YAMLDEFS property maps occupy the
     * ELEMENTLIST directly, without an artificial ELEMENT envelope.
     */
    @Test
    public void AIcIntegratedPropertyMapIsDirectElementListChild() {
        var frontend = new AIcDefsCodegenCanonicalSchemaFrontend(profile());
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            var root = frontend.loadJsonOrYaml(Map.of("type", "object", "properties",
                    Map.of("name", Map.of("type", "string")),
                    "additionalProperties", Map.of("type", "integer")), "map.json", kind);
            var members = (AIcDefsCanonicalElementList) root.structure();
            Assert.assertEquals(members.children().size(), 2);
            Assert.assertEquals(members.children().get(1).kind(),
                    eu.algites.tool.codegen.defs.bootstrap.model.AIngStructureKind_1.MAP);
            var propertyMap = (eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalMap)
                    members.children().get(1);
            Assert.assertEquals(propertyMap.mapKind(),
                    eu.algites.tool.codegen.defs.bootstrap.model.AIngMapKind_1.INTEGRATED_PROPERTY_MAP);
        }
    }

}
