package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIcdKeyDefinition;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import java.util.List;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verifies that the Java canonical representation retains typed keyed values,
 * composite constraints and position-typed array slots without loss of meaning.
 *
 * @author linhart1
 */
public final class AItcMappedFieldCanonicalModelTest {
    /**
     * Validates that multiple key definitions and their ordered field paths
     * survive construction of a typed collection node.
     */
    @Test
    public void AIcCompositeKeysRemainTyped() {
        AIcdDataType locValue = AIcdDataType.object(List.of());
        AIcdKeyDefinition locComposite = new AIcdKeyDefinition(
                "byLocation", List.of("country", "city"), true, false);
        AIcdKeyDefinition locSecondary = new AIcdKeyDefinition(
                "byCode", List.of("code"), true, false);
        AIcdDataType locMap = AIcdDataType.keyedValues(locValue,
                List.of(locComposite, locSecondary));
        Assert.assertEquals(locMap.kind(), AInDataTypeKind.OBJECT);
        Assert.assertSame(locMap.keyedValueType(), locValue);
        Assert.assertEquals(locMap.keyDefinitions(), List.of(locComposite, locSecondary));
        Assert.assertEquals(locMap.keyDefinitions().get(0).fields(), List.of("country", "city"));
    }

    /**
     * Confirms positional slots remain distinct from homogeneous remainder
     * items within the same typed array.
     */
    @Test
    public void AIcPositionalValuesRemainDistinctFromRemainder() {
        AIcdDataType locString = AIcdDataType.atom(AInDataTypeKind.STRING, null);
        AIcdDataType locInteger = AIcdDataType.atom(AInDataTypeKind.INTEGER, null);
        AIcdDataType locBoolean = AIcdDataType.atom(AInDataTypeKind.BOOLEAN, null);
        AIcdDataType locTuple = new AIcdDataType(AInDataTypeKind.ARRAY, locBoolean,
                List.of(), List.of(), null, null, null, List.of(),
                List.of(locString, locInteger));
        Assert.assertEquals(locTuple.positionTypes(), List.of(locString, locInteger));
        Assert.assertSame(locTuple.elementType(), locBoolean);
    }

    /**
     * Ensures that a virtual object key cannot accidentally acquire multiple
     * unrepresentable key components.
     */
    @Test
    public void AIcVirtualCompositeKeyRejected() {
        Assert.expectThrows(IllegalArgumentException.class,
                () -> new AIcdKeyDefinition("bad", List.of("a", "b"), true, true));
    }
}
