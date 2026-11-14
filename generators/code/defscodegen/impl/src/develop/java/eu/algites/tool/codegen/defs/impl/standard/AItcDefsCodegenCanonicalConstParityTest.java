package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.common.AIcCodegenNamingProfileResolver;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngScalarKind_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElement;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalEnum;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Ensures Java and Python frontends use the same lossless singleton-ENUM
 * representation of scalar JSON Schema {@code const} values.
 *
 * @author linhart1
 */
public final class AItcDefsCodegenCanonicalConstParityTest {
    /**
     * Build a minimal naming profile, without hard-coded Java type prefixes.
     * @return profile providing the standard synthetic property role
     */
    private static AIcCodegenNamingProfileResolver.Profile profile() {
        var segment = Map.<String, Object>of("NameFragmentsSegmentValue", Map.of(
                "Kind", "identifier", "Convention", "upper_camel"));
        var composition = Map.<String, Object>of("Segments", List.of(segment));
        return new AIcCodegenNamingProfileResolver.Profile("test", Map.of(),
                Map.of("synthetic_property_type", "compose", "synthetic_inline_enum_type", "compose"), Map.of(),
                Map.of("data_source_schema_url", "$schema"), 1,
                Map.of("compose", composition));
    }

    /**
     * Assert a single fixed literal survives on a generated synthetic type.
     * @param kind JSONDEFS or YAMLDEFS
     * @param literal fixed scalar value
     * @param type optional declared scalar type
     * @param expected resulting canonical scalar kind
     * @param wire expected exact lexical code
     */
    private static void assertConst(AIngSourceInputKind_1 kind, Object literal,
            String type, AIngScalarKind_1 expected, String wire) {
        var constraint = new LinkedHashMap<String, Object>();
        constraint.put("const", literal);
        if (type != null) constraint.put("type", type);
        var schema = Map.<String, Object>of("title", "Holder", "type", "object",
                "properties", Map.of("fixed", constraint));
        var root = new AIcDefsCodegenCanonicalSchemaFrontend(profile())
                .loadJsonOrYaml(schema, "fixed.schema.json", kind);
        var element = (AIcDefsCanonicalElement) ((AIcDefsCanonicalElementList) root.structure())
                .children().get(0);
        var synthetic = (AIcDefsCanonicalType) element.structure();
        var enumType = (AIcDefsCanonicalEnum) synthetic.structure();
        Assert.assertEquals(enumType.baseScalarType(), expected);
        Assert.assertEquals(enumType.values().size(), 1);
        Assert.assertEquals(enumType.values().get(0).wireValue(), wire);
    }

    /** Both frontends preserve string, integer and boolean constants. */
    @Test
    public void scalarConstantsAreTypedAndNotDiscarded() {
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            assertConst(kind, "urn:fixed-schema", "string", AIngScalarKind_1.STRING,
                    "urn:fixed-schema");
            assertConst(kind, 7, "number", AIngScalarKind_1.INTEGER, "7");
            assertConst(kind, true, "boolean", AIngScalarKind_1.BOOLEAN, "true");
        }
    }

    /** Reserved document schema URL does not become a generated DataObject field. */
    @Test
    public void configuredSchemaMetadataIsNotGeneratedAsAField() {
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            var schema = Map.<String, Object>of("type", "object", "properties", Map.of(
                    "$schema", Map.of("type", "string", "const", "urn:representation"),
                    "business", Map.of("type", "string", "const", "value")),
                    "required", List.of("$schema", "business"));
            var type = new AIcDefsCodegenCanonicalSchemaFrontend(profile())
                    .loadJsonOrYaml(schema, "metadata.json", kind);
            var fields = ((AIcDefsCanonicalElementList) type.structure()).children();
            Assert.assertEquals(fields.size(), 1);
            Assert.assertEquals(((AIcDefsCanonicalElement) fields.get(0)).name(), "business");
        }
    }

    /** A contradictory declaration or unsupported fixed structure must fail closed. */
    @Test
    public void invalidConstantsNeverBecomeUnrestrictedStrings() {
        for (var kind : List.of(AIngSourceInputKind_1.JSONDEFS,
                AIngSourceInputKind_1.YAMLDEFS)) {
            var frontend = new AIcDefsCodegenCanonicalSchemaFrontend(profile());
            for (var schema : List.of(
                    Map.<String, Object>of("const", 7, "type", "string"),
                    Map.<String, Object>of("const", true, "enum", List.of(1)),
                    Map.<String, Object>of("const", "ready", "oneOf", List.of(Map.of("type", "string"))),
                    Map.<String, Object>of("const", List.of("a", "b")))) {
                try {
                    frontend.loadJsonOrYaml(schema, "invalid.schema.json", kind);
                    Assert.fail("Const constraints were silently lost: " + schema);
                } catch (IllegalArgumentException | UnsupportedOperationException expected) {
                    Assert.assertNotNull(expected.getMessage());
                }
            }
        }
    }
}
