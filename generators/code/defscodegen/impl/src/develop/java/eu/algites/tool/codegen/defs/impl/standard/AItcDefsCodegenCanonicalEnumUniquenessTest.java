package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.model.*;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalEnum;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalEnumValue;
import eu.algites.tool.codegen.defs.model.AIngScalarKind_1;
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
        for (var kind : List.of(AIngScalarKind_1.INTEGER,
                AIngScalarKind_1.NUMBER, AIngScalarKind_1.BOOLEAN)) {
            List<String> lexical = switch (kind) {
                case INTEGER -> List.of("1", "01");
                case NUMBER -> List.of("1.0", "1.00");
                default -> List.of("true", "1");
            };
            boolean rejected = false;
            try {
                new AIcDefsCanonicalEnum(kind, lexical.stream()
                        .map(value -> new AIcDefsCanonicalEnumValue(value, "")).toList());
            } catch (IllegalArgumentException expected) {
                rejected = expected.getMessage().contains("Duplicate ENUM");
            }
            Assert.assertTrue(rejected);
        }
    }

    /** Retains the original wire spellings and declaration order of distinct values. */
    @Test
    public void AIcCanonicalEnumPreservesDistinctCodes() {
        var values = List.of(new AIcDefsCanonicalEnumValue("001", ""),
                new AIcDefsCanonicalEnumValue("2", ""));
        var definition = new AIcDefsCanonicalEnum(AIngScalarKind_1.INTEGER, values);
        Assert.assertEquals(definition.values(), values);
    }
}
