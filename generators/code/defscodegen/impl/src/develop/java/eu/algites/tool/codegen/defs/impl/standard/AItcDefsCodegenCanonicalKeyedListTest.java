package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.AIcDefsCodegenStructureNormalizer;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenElementList;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenKeyDefinition;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenList;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenScalar;
import eu.algites.tool.codegen.defs.AIcdDefsCodegenType;
import eu.algites.tool.codegen.defs.AInDefsCodegenComposition;
import eu.algites.tool.codegen.defs.AInDefsCodegenResolutionState;
import eu.algites.tool.codegen.defs.AInDefsCodegenScalarKind;
import eu.algites.tool.codegen.defs.AInDefsCodegenTypeOrigin;
import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Regression checks for the source-ordered XML keyed-list model shared by
 * native Java/Python code generation. No legacy backend is involved.
 *
 * @author linhart1
 */
public final class AItcDefsCodegenCanonicalKeyedListTest {
    /**
     * Creates a schema-equivalent declared TYPE with two independent collection
     * key definitions, one composite xs:key and one nullable xs:unique.
     *
     * @return immutable canonical root declaration
     */
    private static AIcdDefsCodegenType sample() {
        var keys = List.of(
                new AIcdDefsCodegenKeyDefinition("employeeCode", "./employee",
                        "/schema/Organization/key[0]", List.of("@department", "personal/code"), true),
                new AIcdDefsCodegenKeyDefinition("uniqueAlias", "./employee",
                        "/schema/Organization/unique[1]", List.of("@alias"), false));
        var list = new AIcdDefsCodegenList("employee", new AIcdDefsCodegenScalar(
                AInDefsCodegenScalarKind.STRING, ""), 0, -1, keys);
        return new AIcdDefsCodegenType("urn:Organization", "Organization",
                AInDefsCodegenTypeOrigin.DECLARED, List.of("Organization"), List.of(),
                new AIcdDefsCodegenElementList(AInDefsCodegenComposition.SEQUENCE,
                        List.of(list), 1, 1), AInDefsCodegenResolutionState.RESOLVED,
                Map.of());
    }

    /**
     * Ensures linker, normalizer, merger, and generated-contract serialization
     * preserve the original XPath values and key/unique distinction.
     */
    @Test
    public void AIcCanonicalKeyedListPreservesCompositePaths() {
        var original = sample();
        var linked = AIcDefsCodegenCanonicalModelLinker.link(List.of(original));
        Assert.assertEquals(linked.size(), 1);
        var root = linked.get(0);
        var group = (AIcdDefsCodegenElementList) root.structure();
        var list = (AIcdDefsCodegenList) group.children().get(0);
        var originalGroup = (AIcdDefsCodegenElementList) original.structure();
        var originalList = (AIcdDefsCodegenList) originalGroup.children().get(0);
        Assert.assertEquals(list.keyDefinitions(), originalList.keyDefinitions());
        Assert.assertEquals(AIcDefsCodegenStructureNormalizer.normalize(original), original);
        var merged = AIcDefsCodegenCanonicalModelMerger.merge(List.of(original, original));
        Assert.assertEquals(merged.get(0).structure(), original.structure());
        var payload = AIcDefsCodegenCanonicalContractPayload.emit(linked);
        String rendered = payload.toString();
        Assert.assertTrue(rendered.contains("@department"));
        Assert.assertTrue(rendered.contains("personal/code"));
        Assert.assertTrue(rendered.contains("uniqueAlias"));
        Assert.assertTrue(rendered.contains("required=false"));
    }

    /**
     * Rejects ambiguous key declarations and prevents unequal key/unique
     * semantics from merging into the same logical collection identity.
     */
    @Test
    public void AIcCanonicalKeyedListRejectsDuplicatesAndConflicts() {
        var key = new AIcdDefsCodegenKeyDefinition("employeeCode", ".", "/key",
                List.of("@id"), true);
        boolean rejected = false;
        try {
            new AIcdDefsCodegenList("employee", new AIcdDefsCodegenScalar(
                    AInDefsCodegenScalarKind.STRING, ""), 0, -1, List.of(key, key));
        } catch (IllegalArgumentException expected) { rejected = true; }
        Assert.assertTrue(rejected);
        var root = sample();
        var group = (AIcdDefsCodegenElementList) root.structure();
        var list = (AIcdDefsCodegenList) group.children().get(0);
        var alternate = new AIcdDefsCodegenList(list.name(), list.item(),
                list.minOccurs(), list.maxOccurs(), List.of(
                    new AIcdDefsCodegenKeyDefinition("employeeCode", "./employee",
                            "/schema/Organization/key[0]", List.of("@department", "personal/code"), false),
                    list.keyDefinitions().get(1)));
        var other = new AIcdDefsCodegenType(root.identity(), root.name(), root.origin(),
                root.pathSegments(), root.inheritedFromTypes(),
                new AIcdDefsCodegenElementList(group.composition(), List.of(alternate),
                        group.minOccurs(), group.maxOccurs()), root.resolutionState(),
                root.sourceBindings());
        rejected = false;
        try {
            AIcDefsCodegenCanonicalModelMerger.merge(List.of(root, other));
        } catch (IllegalArgumentException expected) {
            rejected = expected.getMessage().contains("key definitions");
        }
        Assert.assertTrue(rejected);
    }
}
