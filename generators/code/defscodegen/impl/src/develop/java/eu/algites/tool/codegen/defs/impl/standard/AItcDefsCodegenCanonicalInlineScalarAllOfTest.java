package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalScalar;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Native Java regressions for scalar JSON Schema and YAMLDEFS conjunctions.
 * This exercises the frontend's isolated normalization before model allocation;
 * the immutable bootstrap *.extgen model must be regenerated separately.
 *
 * @author linhart1
 */
public final class AItcDefsCodegenCanonicalInlineScalarAllOfTest {
    /**
     * Invoke the scalar conjunction normalizer without requiring regenerated
     * canonical bootstrap SDO classes in the test classpath.
     *
     * @param schema inline allOf source
     * @return effective scalar restrictions
     * @throws ReflectiveOperationException if the implementation entrypoint changes
     */
    private static AIcDefsCanonicalScalar normalized(Map<String, Object> schema)
            throws ReflectiveOperationException {
        Method method = AIcDefsCodegenCanonicalSchemaFrontend.class.getDeclaredMethod(
                "jsonInlineScalarAllOf", Map.class, String.class);
        method.setAccessible(true);
        return (AIcDefsCanonicalScalar) method.invoke(null, schema, "#/properties/value");
    }

    /** Test that string facets from all parts survive in their effective form. */
    @Test
    public void AIcInlineStringAllOfRetainsEffectiveFacets() throws ReflectiveOperationException {
        Map<String, Object> schema = Map.of("type", "string", "minLength", 2,
                "allOf", List.of(Map.of("minLength", 3),
                        Map.of("maxLength", 8), Map.of("pattern", "[A-Z]+")));
        var scalar = normalized(schema);
        Assert.assertEquals(scalar.minLength(), 3);
        Assert.assertEquals(scalar.maxLength(), 8);
        Assert.assertEquals(scalar.pattern(), "[A-Z]+");
    }

    /** Test numeric type intersection, exclusive limits and rejection of conflicts. */
    @Test
    public void AIcInlineNumericAllOfRetainsExclusiveBounds() throws ReflectiveOperationException {
        Map<String, Object> schema = Map.of("type", "integer", "minimum", 0,
                "allOf", List.of(Map.of("type", "number", "minimum", 5),
                        Map.of("exclusiveMinimum", 5), Map.of("maximum", 10)));
        var scalar = normalized(schema);
        Assert.assertEquals(scalar.minimum(), "5");
        Assert.assertEquals(scalar.maximum(), "10");
        Assert.assertTrue(scalar.exclusiveMinimum());
    }

    /** Conflicting restrictions must fail instead of generating weakened annotations. */
    @Test
    public void AIcInlineScalarAllOfRejectsLossyIntersections() throws ReflectiveOperationException {
        for (var schema : List.<Map<String, Object>>of(
                Map.of("type", "string", "allOf", List.of(
                        Map.of("minLength", 5), Map.of("maxLength", 4))),
                Map.of("type", "string", "allOf", List.of(
                        Map.of("pattern", "A+"), Map.of("pattern", "B+"))))) {
            try {
                normalized(schema);
                Assert.fail("A scalar intersection lost a required facet");
            } catch (InvocationTargetException expected) {
                Assert.assertTrue(expected.getCause() instanceof IllegalArgumentException
                        || expected.getCause() instanceof UnsupportedOperationException,
                        String.valueOf(expected.getCause()));
            }
        }
    }
}
