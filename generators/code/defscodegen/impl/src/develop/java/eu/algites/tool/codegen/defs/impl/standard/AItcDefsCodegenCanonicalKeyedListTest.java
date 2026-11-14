package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.bootstrap.model.*;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalStructureNormalizer;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalKeyDefinition;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalScalar;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngComposition_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngResolutionState_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngScalarKind_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngTypeOrigin_1;
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
    private static AIcDefsCanonicalType sample() {
        var keys = List.of(
                new AIcDefsCanonicalKeyDefinition("employeeCode", "./employee",
                        "/schema/Organization/key[0]", List.of("@department", "personal/code"), true),
                new AIcDefsCanonicalKeyDefinition("uniqueAlias", "./employee",
                        "/schema/Organization/unique[1]", List.of("@alias"), false));
        var list = new AIcDefsCanonicalList("employee", new AIcDefsCanonicalScalar(
                AIngScalarKind_1.STRING, ""), 0, -1, keys);
        return new AIcDefsCanonicalType("urn:Organization", "Organization",
                AIngTypeOrigin_1.DECLARED, List.of("Organization"), List.of(),
                new AIcDefsCanonicalElementList(AIngComposition_1.SEQUENCE,
                        List.of(list), 1, 1), AIngResolutionState_1.RESOLVED,
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
        var group = (AIcDefsCanonicalElementList) root.structure();
        var list = (AIcDefsCanonicalList) group.children().get(0);
        var originalGroup = (AIcDefsCanonicalElementList) original.structure();
        var originalList = (AIcDefsCanonicalList) originalGroup.children().get(0);
        Assert.assertEquals(list.keyDefinitions(), originalList.keyDefinitions());
        Assert.assertEquals(AIcDefsCanonicalStructureNormalizer.normalize(original), original);
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
        var key = new AIcDefsCanonicalKeyDefinition("employeeCode", ".", "/key",
                List.of("@id"), true);
        boolean rejected = false;
        try {
            new AIcDefsCanonicalList("employee", new AIcDefsCanonicalScalar(
                    AIngScalarKind_1.STRING, ""), 0, -1, List.of(key, key));
        } catch (IllegalArgumentException expected) { rejected = true; }
        Assert.assertTrue(rejected);
        var root = sample();
        var group = (AIcDefsCanonicalElementList) root.structure();
        var list = (AIcDefsCanonicalList) group.children().get(0);
        var alternate = new AIcDefsCanonicalList(list.name(), list.item(),
                list.minItemCount(), list.maxItemCount(), List.of(
                    new AIcDefsCanonicalKeyDefinition("employeeCode", "./employee",
                            "/schema/Organization/key[0]", List.of("@department", "personal/code"), false),
                    list.keyDefinitions().get(1)));
        var other = new AIcDefsCanonicalType(root.identity(), root.name(), root.origin(),
                root.pathSegments(), root.inheritedFromTypes(),
                new AIcDefsCanonicalElementList(group.composition(), List.of(alternate),
                        group.minItemCount(), group.maxItemCount()), root.resolutionState(),
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
