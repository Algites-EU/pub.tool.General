package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.lib.data.dataobject.AInFieldPresenceKind;
import eu.algites.tool.codegen.defs.AIcdCanonicalDefinition;
import eu.algites.tool.codegen.defs.AIcdDataType;
import eu.algites.tool.codegen.defs.AIcdDefinitionReference;
import eu.algites.tool.codegen.defs.AIcdPropertyDefinition;
import eu.algites.tool.codegen.defs.AInDataTypeKind;
import eu.algites.tool.codegen.defs.AInDefinitionSourceKind;
import java.util.Arrays;
import java.util.List;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Confirms the canonical API has no obsolete flat fields and compares genuinely recursive shapes.
 * No schema-format frontend or external generator runtime is required by these tests.
 */
public final class AItcRecursiveCanonicalModelTest {
    private static AIcdCanonicalDefinition definition(AInDefinitionSourceKind aSourceKind,
            AIcdDataType aMemberType) {
        AIcdPropertyDefinition locProperty = new AIcdPropertyDefinition(
                "Items", aMemberType, AInFieldPresenceKind.REQUIRED, false, null, null, null);
        return new AIcdCanonicalDefinition("urn:recursive", 1, "recursive", aSourceKind,
                "recursive_1", null, AIcdDataType.object(List.of(locProperty)), List.of(), null);
    }

    /** The canonical definition and its fields expose exactly one structural data type. */
    @Test
    public void AIcCanonicalTypesDoNotRetainFlatProjections() {
        List<String> locDefinitionComponents = Arrays.stream(AIcdCanonicalDefinition.class.getRecordComponents())
                .map(java.lang.reflect.RecordComponent::getName).toList();
        List<String> locPropertyComponents = Arrays.stream(AIcdPropertyDefinition.class.getRecordComponents())
                .map(java.lang.reflect.RecordComponent::getName).toList();
        Assert.assertTrue(locDefinitionComponents.contains("dataType"));
        Assert.assertFalse(locDefinitionComponents.contains("kind"));
        Assert.assertFalse(locDefinitionComponents.contains("properties"));
        List<String> locReferenceComponents = Arrays.stream(AIcdDefinitionReference.class.getRecordComponents())
                .map(java.lang.reflect.RecordComponent::getName).toList();
        Assert.assertTrue(locReferenceComponents.contains("targetDataType"));
        Assert.assertFalse(locReferenceComponents.contains("targetKind"));
        Assert.assertTrue(locPropertyComponents.contains("dataType"));
        for (String locFormer : List.of("valueKind", "itemValueKind", "reference", "constraints", "required"))
            Assert.assertFalse(locPropertyComponents.contains(locFormer));
    }

    /** Scalar members compare safely without dereferencing a nonexistent array element. */
    @Test
    public void AIcScalarDefinitionsMergeWithoutFlatArrayAccess() {
        AIcdDataType locString = AIcdDataType.atom(AInDataTypeKind.STRING, null);
        AIcCanonicalDefinitionMerger.AIcMerge(List.of(
                definition(AInDefinitionSourceKind.JSONDEFS, locString),
                definition(AInDefinitionSourceKind.YAMLDEFS, locString)));
    }

    /** A changed alternative within nested arrays must produce a structural conflict. */
    @Test
    public void AIcNestedChoiceChangeIsRejected() {
        AIcdDataType locBase = AIcdDataType.array(AIcdDataType.choice(AInDataTypeKind.ONE_OF,
                List.of(AIcdDataType.atom(AInDataTypeKind.STRING, null),
                        AIcdDataType.atom(AInDataTypeKind.INTEGER, null))));
        AIcdDataType locChanged = AIcdDataType.array(AIcdDataType.choice(AInDataTypeKind.ONE_OF,
                List.of(AIcdDataType.atom(AInDataTypeKind.STRING, null),
                        AIcdDataType.atom(AInDataTypeKind.BOOLEAN, null))));
        String locMessage = Assert.expectThrows(IllegalArgumentException.class,
                () -> AIcCanonicalDefinitionMerger.AIcMerge(List.of(
                        definition(AInDefinitionSourceKind.JSONDEFS, locBase),
                        definition(AInDefinitionSourceKind.YAMLDEFS, locChanged)))).getMessage();
        Assert.assertTrue(locMessage.contains("dataType.items.alternatives[1].kind"));
    }
}
