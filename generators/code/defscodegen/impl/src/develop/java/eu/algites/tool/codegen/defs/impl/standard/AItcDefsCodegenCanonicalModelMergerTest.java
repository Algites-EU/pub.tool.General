package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.bootstrap.model.*;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElement;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalScalar;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalSourceBinding;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import eu.algites.tool.codegen.defs.impl.standard.model.AIiDefsCanonicalStructure;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngComposition_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngResolutionState_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngScalarKind_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngTypeOrigin_1;
import java.util.List;
import java.util.Map;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * Verifies Java/Python parity of provenance accumulation and fail-closed source
 * reconciliation without involving the deprecated native generator model.
 */
public final class AItcDefsCodegenCanonicalModelMergerTest {
    /**
     * Creates one root with a nested member, using stable identity but distinct
     * source resource bindings for each source technology.
     *
     * @param inputKind input schema family, such as JSONDEFS or YAMLDEFS
     * @param resource original source document name
     * @param scalarKind scalar kind of the member's value
     * @return canonical root with source bindings at both TYPE and ELEMENT level
     */
    private static AIcDefsCanonicalType root(AIngSourceInputKind_1 inputKind,
            String resource, AIngScalarKind_1 scalarKind) {
        var bindings = Map.of(inputKind,
                List.of(new AIcDefsCanonicalSourceBinding(resource, "#/properties/id", "properties")));
        AIiDefsCanonicalStructure structure = new AIcDefsCanonicalElementList(
                AIngComposition_1.SEQUENCE, List.of(new AIcDefsCanonicalElement(
                        "id", new AIcDefsCanonicalScalar(scalarKind, ""), List.of(), bindings)));
        return new AIcDefsCanonicalType("customer", "Customer", AIngTypeOrigin_1.DECLARED,
                List.of("Customer"), List.of(), structure, AIngResolutionState_1.RESOLVED,
                bindings);
    }

    /**
     * Two independent representation families of one logical type should produce
     * one declaration whose nested source bindings contain both original locations.
     */
    @Test
    public void AIcMergeTwoSourceTechnologiesWithoutOverwriting() {
        var json = root(AIngSourceInputKind_1.JSONDEFS, "a.json", AIngScalarKind_1.STRING);
        var yaml = root(AIngSourceInputKind_1.YAMLDEFS, "b.yaml", AIngScalarKind_1.STRING);
        var merged = AIcDefsCodegenCanonicalModelMerger.merge(List.of(json, yaml));
        Assert.assertEquals(merged.size(), 1);
        Assert.assertEquals(merged.get(0).sourceBindings().size(), 2);
        var member = (AIcDefsCanonicalElement) ((AIcDefsCanonicalElementList)
                merged.get(0).structure()).children().get(0);
        Assert.assertEquals(member.sourceBindings().size(), 2);
        Assert.assertEquals(member.sourceBindings().get(AIngSourceInputKind_1.YAMLDEFS)
                .get(0).sourceResource(), "b.yaml");
        Assert.assertEquals(AIcDefsCodegenCanonicalModelLinker.link(merged).size(), 1);
    }

    /**
     * Multiple source files of the same technology must append bindings in their
     * source order instead of replacing the first resource's member provenance.
     */
    @Test
    public void AIcMergeRepeatedBindingsForOneTechnologyInOrder() {
        var first = root(AIngSourceInputKind_1.JSONDEFS, "first.json", AIngScalarKind_1.STRING);
        var second = root(AIngSourceInputKind_1.JSONDEFS, "second.json", AIngScalarKind_1.STRING);
        var merged = AIcDefsCodegenCanonicalModelMerger.merge(List.of(first, second));
        Assert.assertEquals(merged.get(0).sourceBindings().get(AIngSourceInputKind_1.JSONDEFS)
                .stream().map(AIcDefsCanonicalSourceBinding::sourceResource).toList(),
                List.of("first.json", "second.json"));
    }

    /**
     * Equivalent names with incompatible scalar semantics are rejected with their
     * nested canonical path rather than silently choosing the last source file.
     */
    @Test
    public void AIcConflictReportsExactMemberPath() {
        var first = root(AIngSourceInputKind_1.JSONDEFS, "first.json", AIngScalarKind_1.STRING);
        var second = root(AIngSourceInputKind_1.YAMLDEFS, "second.yaml", AIngScalarKind_1.INTEGER);
        try {
            AIcDefsCodegenCanonicalModelMerger.merge(List.of(first, second));
            Assert.fail("Incompatible representations must fail closed");
        } catch (IllegalArgumentException expected) {
            Assert.assertTrue(expected.getMessage().contains("customer/structure/children/0/id"));
            Assert.assertTrue(expected.getMessage().contains("scalar"));
            Assert.assertTrue(expected.getMessage().contains("first.json#/properties/id"));
            Assert.assertTrue(expected.getMessage().contains("second.yaml#/properties/id"));
        }
    }
}
