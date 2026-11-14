package eu.algites.tool.codegen.defs.impl.standard;

import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Regression checks for the native Java canonical-model JSON Schema validator.
 * The Java CLI must not bypass schema constraints that Python enforces.
 *
 * @author linhart1
 */
public final class AItcDefsCodegenCanonicalSchemaValidatorTest {
    /**
     * Construct a small self-contained schema with references and closed choices.
     * @return parsed schema equivalent to canonical model's simple oneOf pattern
     */
    private static Map<String, Object> schema() {
        return Map.of("$id", "urn:test", "type", "object", "$defs", Map.of(
                "Choice", Map.of("type", "object", "minProperties", 1, "maxProperties", 1,
                        "properties", Map.of("Type", Map.of("$ref", "#/$defs/Scalar"),
                                "Scalar", Map.of("$ref", "#/$defs/Scalar")),
                        "additionalProperties", false),
                "Scalar", Map.of("type", "object", "properties", Map.of(
                        "format", Map.of("type", "string")),
                        "required", List.of("format"), "additionalProperties", false)),
                "properties", Map.of("node", Map.of("$ref", "#/$defs/Choice")),
                "required", List.of("node"), "additionalProperties", false);
    }

    /** Verify valid recursively referenced canonical choice. */
    @Test
    public void acceptsValidClosedCanonicalNode() {
        new AIcDefsCodegenCanonicalSchemaValidator(schema()).validate(Map.of(
                "node", Map.of("Scalar", Map.of("format", ""))));
    }

    /** Verify that alternatives and unknown keys cannot silently disappear. */
    @Test
    public void rejectsInvalidCanonicalNodes() {
        var validator = new AIcDefsCodegenCanonicalSchemaValidator(schema());
        for (var incorrect : List.<Map<String, Object>>of(
                Map.of("node", Map.of()),
                Map.of("node", Map.of("Scalar", Map.of("format", ""),
                        "Type", Map.of("format", ""))),
                Map.of("node", Map.of("Unknown", Map.of("format", ""))),
                Map.of("node", Map.of("Scalar", Map.of("oops", "lost"))))) {
            try {
                validator.validate(incorrect);
                Assert.fail("Invalid canonical model was accepted: " + incorrect);
            } catch (IllegalArgumentException expected) {
                Assert.assertTrue(expected.getMessage().contains("canonical model"));
            }
        }
    }

    /** Refuse schema vocabulary which the native Java validator cannot check. */
    @Test
    public void rejectsUnsupportedCanonicalSchemaKeyword() {
        try {
            new AIcDefsCodegenCanonicalSchemaValidator(Map.of("type", "string", "contains", Map.of()));
            Assert.fail("Unsupported validation keyword was ignored");
        } catch (UnsupportedOperationException expected) {
            Assert.assertTrue(expected.getMessage().contains("contains"));
        }
    }
}
