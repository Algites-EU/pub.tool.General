package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.bootstrap.model.AIngComposition_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngResolutionState_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngScalarKind_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngTypeOrigin_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIigStructureVariantElementList2_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIigTypeContentVariantStructure1_1;
import eu.algites.tool.codegen.defs.bootstrap.model.impl.AIcgdElement_1;
import eu.algites.tool.codegen.defs.bootstrap.model.impl.AIcgdScalar_1;
import eu.algites.tool.codegen.defs.bootstrap.model.impl.AIcgdSourceBindings_1;
import eu.algites.tool.codegen.defs.bootstrap.model.impl.AIcgdType_1;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElement;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalScalar;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalSourceBinding;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import java.lang.reflect.Modifier;
import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Protects the Java canonical frontend against reintroducing a handwritten
 * canonical DTO. All readable fields must be stored in schema-generated SDOs.
 *
 * @author linhart1
 */
public final class AItcDefsCodegenCanonicalGeneratedSdoTest {
    /**
     * Confirms that the fully typed, sealed graph consists of generated SDOs
     * and that the read-only views do not contain shadow state.
     */
    @Test
    public void AIcJavaCanonicalNodesAreGeneratedSdoObjectsWithoutShadowFields() {
        var scalar = new AIcDefsCanonicalScalar(AIngScalarKind_1.STRING, "");
        var element = new AIcDefsCanonicalElement("name", scalar, List.of(), Map.of());
        var group = new AIcDefsCanonicalElementList(AIngComposition_1.SEQUENCE, List.of(element));
        var original = new AIcDefsCanonicalType("urn:person", "Person",
                AIngTypeOrigin_1.DECLARED, List.of("Person"), List.of(), group,
                AIngResolutionState_1.RESOLVED, Map.of());

        Assert.assertTrue(original instanceof AIcgdType_1);
        Assert.assertTrue(element instanceof AIcgdElement_1);
        Assert.assertTrue(scalar instanceof AIcgdScalar_1);
        Assert.assertTrue(original.getContent() instanceof AIigTypeContentVariantStructure1_1);
        Assert.assertTrue(((AIigTypeContentVariantStructure1_1) original.getContent())
                .getStructure() instanceof AIigStructureVariantElementList2_1);
        Assert.assertEquals(original.getIdentity(), "urn:person");
        Assert.assertEquals(original.structure(), group);
        Assert.assertEquals(((AIcDefsCanonicalElementList) original.structure()).children(), List.of(element));
        for (Class<?> view : List.of(AIcDefsCanonicalType.class,
                AIcDefsCanonicalElement.class, AIcDefsCanonicalScalar.class)) {
            for (var field : view.getDeclaredFields()) {
                Assert.assertTrue(Modifier.isStatic(field.getModifiers()));
            }
        }
    }

    /**
     * Verifies that the source provenance uses the actual multi-mapped SDO
     * collection, not an independently stored Java map.
     */
    @Test
    public void AIcJavaCanonicalSourceBindingsAreGeneratedMultiMappedSdo() {
        var input = new AIcDefsCanonicalSourceBinding("test.json", "#/properties/name", "properties");
        var type = new AIcDefsCanonicalType("urn:person", "Person", AIngTypeOrigin_1.DECLARED,
                List.of("Person"), List.of(),
                new AIcDefsCanonicalScalar(AIngScalarKind_1.STRING, ""),
                AIngResolutionState_1.RESOLVED,
                Map.of(AIngSourceInputKind_1.JSONDEFS, List.of(input)));
        Assert.assertTrue(type.getSourceBindings() instanceof AIcgdSourceBindings_1);
        Assert.assertEquals(type.sourceBindings().get(AIngSourceInputKind_1.JSONDEFS), List.of(input));
        var sourceGroup = type.getSourceBindings().getSourceBindingGroupList().get(0);
        Assert.assertEquals(sourceGroup.getInputKind(), AIngSourceInputKind_1.JSONDEFS);
        Assert.assertEquals(sourceGroup.getBindingList().size(), 1);
        Assert.assertEquals(AIcDefsCodegenCanonicalContractPayload.emit(List.of(type))
                .get("types") instanceof List<?>, true);
    }
    /**
     * Exercises the named TypeContent choice, covariant generated Java list
     * contracts, keyed members, bounded groups, and unresolved references.
     * A pending TYPE intentionally leaves Content absent until linking.
     */
    @Test
    public void AIcJavaCanonicalTypeContentAndCollectionContractsAreLive() {
        var scalar = new AIcDefsCanonicalScalar(AIngScalarKind_1.STRING, "");
        var key = new eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalKeyDefinition(
                "unique-name", ".", "#/properties/name", List.of("name"), true);
        var member = new AIcDefsCanonicalElement("name", scalar, List.of(key), Map.of());
        var list = new eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalList(
                "entries", member, 0, -1, List.of(key));
        var group = new AIcDefsCanonicalElementList(AIngComposition_1.SEQUENCE,
                List.of(member, list), 2, 5, 1, 3);
        Assert.assertEquals(group.minItemCount(), 2);
        Assert.assertEquals(group.maxItemCount(), 5);
        Assert.assertEquals(group.children().size(), 2);
        Assert.assertEquals(list.keyDefinitions().get(0).fields(), List.of("name"));

        var structured = new AIcDefsCanonicalType("urn:structured", "Structured",
                AIngTypeOrigin_1.DECLARED, List.of("Structured"), List.of("Base"), group,
                AIngResolutionState_1.RESOLVED, Map.of());
        Assert.assertEquals(structured.structure(), group);
        Assert.assertEquals(structured.pathSegments(), List.of("Structured"));
        Assert.assertEquals(structured.inheritedFromTypes(), List.of("Base"));
        Assert.assertEquals(structured.targetIdentity(), "");
        Assert.assertEquals(structured.sourceBindings(), Map.of());

        var linked = new AIcDefsCanonicalType("urn:ref", "Reference",
                AIngTypeOrigin_1.DECLARED, List.of(), List.of(), null,
                AIngResolutionState_1.RESOLVED, Map.of(), "urn:structured");
        Assert.assertEquals(linked.targetIdentity(), "urn:structured");
        Assert.assertNull(linked.structure());

        var pending = new AIcDefsCanonicalType("urn:pending", "Pending",
                AIngTypeOrigin_1.DECLARED, List.of(), List.of(), null,
                AIngResolutionState_1.REFERENCE, Map.of());
        Assert.assertNull(pending.structure());
        Assert.assertEquals(pending.targetIdentity(), "");
    }

}
