package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElement;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalEnum;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verifies neutral owner-plus-member naming for inline JSONDEFS/YAMLDEFS enums.
 * Named enum references remain nominal; inline object fields keep their own
 * naming role. The same conventions are applied in the XSD frontend.
 *
 * @author linhart1
 */
public final class AItcDefsCodegenCanonicalInlineEnumNamingTest {
    /**
     * Build independent role compositions without coupling the test to a profile file.
     * @return explicitly configured test-only naming profile
     */
    private static AIcCodegenNamingProfileResolver.Profile profile() {
        var owner = Map.<String, Object>of("NameFragmentsSegmentValue", Map.of(
                "Kind", "variable", "Name", "owner_type", "Regexp", ".+"));
        var member = Map.<String, Object>of("NameFragmentsSegmentValue", Map.of(
                "Kind", "identifier", "Convention", "upper_camel"));
        var marker = Map.<String, Object>of("NameFragmentsSegmentValue", Map.of(
                "Kind", "constant_string", "Value", "Property"));
        var enumName = Map.<String, Object>of("Segments", List.of(owner, member));
        var propertyName = Map.<String, Object>of("Segments", List.of(owner, marker, member));
        return new AIcCodegenNamingProfileResolver.Profile("test", Map.of(),
                Map.of("synthetic_inline_enum_type", "inline-enum",
                       "synthetic_property_type", "property"),
                Map.of(), Map.of(), 1,
                Map.of("inline-enum", enumName, "property", propertyName));
    }

    /** JSON Schema and YAMLDEFS generate the same nominal enum name. */
    @Test
    public void inlineEnumUsesSharedNamingRole() {
        var source = Map.<String, Object>of("title", "Person", "type", "object",
                "properties", Map.of(
                        "Status", Map.of("type", "string", "enum", List.of("active", "inactive")),
                        "Fixed", Map.of("type", "string", "const", "ready"),
                        "Details", Map.of("type", "object", "properties", Map.of(
                                "name", Map.of("type", "string")))));
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS, AIngSourceInputKind_1.YAMLDEFS)) {
            var result = new AIcDefsCodegenCanonicalSchemaFrontend(profile())
                    .loadJsonOrYaml(source, "person.schema.json", kind);
            var fields = ((AIcDefsCanonicalElementList) result.structure()).children();
            var keyed = fields.stream().map(node -> (AIcDefsCanonicalElement) node)
                    .collect(java.util.stream.Collectors.toMap(AIcDefsCanonicalElement::name,
                            AIcDefsCanonicalElement::structure));
            var status = (AIcDefsCanonicalType) keyed.get("Status");
            var fixed = (AIcDefsCanonicalType) keyed.get("Fixed");
            var details = (AIcDefsCanonicalType) keyed.get("Details");
            Assert.assertEquals(status.name(), "PersonStatus");
            Assert.assertEquals(fixed.name(), "PersonFixed");
            Assert.assertEquals(details.name(), "PersonPropertyDetails");
            Assert.assertTrue(status.structure() instanceof AIcDefsCanonicalEnum);
            Assert.assertTrue(fixed.structure() instanceof AIcDefsCanonicalEnum);
        }
    }

    /**
     * Synthesized JSONDEFS/YAMLDEFS types receive their source document's
     * version even when one frontend processes multiple documents.
     */
    @Test
    public void syntheticTypesUseOwnDocumentVersionForJsonAndYaml() {
        var source = Map.<String, Object>of("type", "object", "properties", Map.of(
                "Status", Map.of("type", "string", "enum", List.of("on", "off")),
                "Details", Map.of("type", "object", "properties", Map.of(
                        "Name", Map.of("type", "string")))));
        var frontend = new AIcDefsCodegenCanonicalSchemaFrontend(profile());
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS, AIngSourceInputKind_1.YAMLDEFS)) {
            for (var version : List.of("1", "7")) {
                var type = frontend.loadJsonOrYaml(source, "person_" + version + kind,
                        kind, "Person", version);
                Assert.assertEquals(type.schemaVersion(), version);
                var fields = ((AIcDefsCanonicalElementList) type.structure()).children();
                for (var node : fields) {
                    var generated = (AIcDefsCanonicalType) ((AIcDefsCanonicalElement) node).structure();
                    Assert.assertEquals(generated.schemaVersion(), version);
                }
            }
        }
    }

    /** XSD inline types inherit the version of the enclosing XSD. */
    @Test
    public void xmlSyntheticTypesUseOwnDocumentVersion() {
        var frontend = new AIcDefsCodegenCanonicalSchemaFrontend(profile());
        var schema = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\">"
                + "<xs:complexType name=\"Person\"><xs:sequence>"
                + "<xs:element name=\"Status\"><xs:simpleType><xs:restriction base=\"xs:string\">"
                + "<xs:enumeration value=\"on\"/><xs:enumeration value=\"off\"/>"
                + "</xs:restriction></xs:simpleType></xs:element>"
                + "</xs:sequence></xs:complexType></xs:schema>";
        for (var version : List.of("1", "7")) {
            var root = frontend.loadXsd(schema, "person_" + version + ".xsd", version).get(0);
            Assert.assertEquals(root.schemaVersion(), version);
            var field = (AIcDefsCanonicalElement) ((AIcDefsCanonicalElementList)
                    root.structure()).children().get(0);
            Assert.assertEquals(((AIcDefsCanonicalType) field.structure()).schemaVersion(), version);
        }
    }

    /** Anonymous XML element enum uses precisely the same owner/member role. */
    @Test
    public void xmlInlineEnumMatchesJsonYamlName() {
        String xsd = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\">"
                + "<xs:complexType name=\"Person\"><xs:sequence>"
                + "<xs:element name=\"Status\"><xs:simpleType><xs:restriction base=\"xs:string\">"
                + "<xs:enumeration value=\"active\"/><xs:enumeration value=\"inactive\"/>"
                + "</xs:restriction></xs:simpleType></xs:element>"
                + "</xs:sequence></xs:complexType></xs:schema>";
        var person = new AIcDefsCodegenCanonicalSchemaFrontend(profile())
                .loadXsd(xsd, "person.xsd").get(0);
        var field = (AIcDefsCanonicalElement) ((AIcDefsCanonicalElementList)
                person.structure()).children().get(0);
        Assert.assertEquals(((AIcDefsCanonicalType) field.structure()).name(), "PersonStatus");
    }
}
