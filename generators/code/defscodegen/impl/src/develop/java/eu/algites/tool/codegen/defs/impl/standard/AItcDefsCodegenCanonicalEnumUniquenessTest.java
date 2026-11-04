package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcdDefsCodegenEnum;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenEnumValue;
import eu.algites.tool.codegen.defs.AInDefsCodegenScalarKind;
import java.util.List;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verifies canonical enum uniqueness by semantic typed value instead of raw
 * XML/JSON lexical representation, with parity across Java and Python.
 *
 * @author linhart1
 */
public final class AItcDefsCodegenCanonicalEnumUniquenessTest {
    /** Rejects duplicate integers with different legal XML lexical spellings. */
    @Test
    public void AIcCanonicalEnumRejectsNumericallyEquivalentCodes() {
        for (var kind : List.of(AInDefsCodegenScalarKind.INTEGER,
                AInDefsCodegenScalarKind.NUMBER, AInDefsCodegenScalarKind.BOOLEAN)) {
            List<String> lexical = switch (kind) {
                case INTEGER -> List.of("1", "01");
                case NUMBER -> List.of("1.0", "1.00");
                default -> List.of("true", "1");
            };
            boolean rejected = false;
            try {
                new AIcdDefsCodegenEnum(kind, lexical.stream()
                        .map(value -> new AIcdDefsCodegenEnumValue(value, "")).toList());
            } catch (IllegalArgumentException expected) {
                rejected = expected.getMessage().contains("Duplicate ENUM");
            }
            Assert.assertTrue(rejected);
        }
    }

    /** Retains the original wire spellings and declaration order of distinct values. */
    @Test
    public void AIcCanonicalEnumPreservesDistinctCodes() {
        var values = List.of(new AIcdDefsCodegenEnumValue("001", ""),
                new AIcdDefsCodegenEnumValue("2", ""));
        var definition = new AIcdDefsCodegenEnum(AInDefsCodegenScalarKind.INTEGER, values);
        Assert.assertEquals(definition.values(), values);
    }
}
