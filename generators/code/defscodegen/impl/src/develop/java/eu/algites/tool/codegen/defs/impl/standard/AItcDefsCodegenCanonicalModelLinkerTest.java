package eu.algites.tool.codegen.defs.impl.standard;

import eu.algites.tool.codegen.defs.impl.standard.model.*;
import eu.algites.tool.codegen.defs.bootstrap.model.*;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElement;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalElementList;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalScalar;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalSourceBinding;
import eu.algites.tool.codegen.defs.impl.standard.model.AIcDefsCanonicalType;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngComposition_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngResolutionState_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngScalarKind_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngSourceInputKind_1;
import eu.algites.tool.codegen.defs.bootstrap.model.AIngTypeOrigin_1;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * End-to-end Java reference-linker regressions for recursive XMLDEFS/JSONDEFS/YAMLDEFS
 * contracts, stable source bindings and ordered post-validation normalization.
 */
public final class AItcDefsCodegenCanonicalModelLinkerTest {
    /**
     * Builds an immutable resolved declaration using one exact resource location.
     *
     * @param identity canonical declaration identity
     * @param name source-derived type name
     * @param resource source document containing the declaration
     * @param pointer source pointer, including {@code #} for a document root
     * @param structure canonical declaration structure
     * @return validated resolved TYPE retaining its original source location
     */
    private static AIcDefsCanonicalType declared(String identity, String name, String resource,
            String pointer, eu.algites.tool.codegen.defs.impl.standard.model.AIiDefsCanonicalStructure structure) {
        return new AIcDefsCanonicalType(identity, name, AIngTypeOrigin_1.DECLARED,
                List.of(name), List.of(), structure, AIngResolutionState_1.RESOLVED,
                binding(resource, pointer));
    }

    /**
     * Creates a reference in the same resource without resolving its TYPE target.
     *
     * @param identity symbolic target identity, including possible JSON Pointer fragments
     * @param resource the referring source document
     * @param pointer exact source location of the reference
     * @return pending reference with source provenance, ready for the linker
     */
    private static AIcDefsCanonicalType reference(String identity, String resource, String pointer) {
        return new AIcDefsCanonicalType(identity, identity, AIngTypeOrigin_1.DECLARED,
                List.of(identity), List.of(), null, AIngResolutionState_1.REFERENCE,
                binding(resource, pointer));
    }

    /**
     * Creates one JSONDEFS source binding; production parsing can also supply XMLDEFS
     * and YAMLDEFS, which the linker traverses without rewriting provenance.
     *
     * @param resource source URI or source file identifier
     * @param pointer original source JSON Pointer
     * @return source-typed immutable binding collection
     */
    private static Map<AIngSourceInputKind_1, List<AIcDefsCanonicalSourceBinding>>
            binding(String resource, String pointer) {
        return Map.of(AIngSourceInputKind_1.JSONDEFS,
                List.of(new AIcDefsCanonicalSourceBinding(resource, pointer, "reference")));
    }

    /**
     * Verifies that a self-recursive schema resolves to a symbolic link, not a cyclic
     * Java value graph, and that the full provenance survives contract projection.
     */
    @Test
    public void AIcSelfRecursiveRootReferenceIsSymbolic() {
        var root = declared("urn:node", "Node", "node.json", "#",
                new AIcDefsCanonicalElementList(AIngComposition_1.SEQUENCE, List.of(
                        new AIcDefsCanonicalElement("child", reference("#", "node.json",
                                "#/properties/child"), List.of(), binding("node.json", "#/properties/child")))));
        var result = AIcDefsCodegenCanonicalModelLinker.link(List.of(root));
        var member = (AIcDefsCanonicalElement) ((AIcDefsCanonicalElementList)
                result.get(0).structure()).children().get(0);
        var resolved = (AIcDefsCanonicalType) member.structure();
        Assert.assertEquals(resolved.targetIdentity(), "urn:node");
        Assert.assertNull(resolved.structure());
        Assert.assertEquals(resolved.sourceBindings().get(AIngSourceInputKind_1.JSONDEFS)
                .get(0).sourcePointer(), "#/properties/child");
        Assert.assertNotNull(AIcDefsCodegenCanonicalContractPayload.emit(result));
    }

    /**
     * Verifies that similarly named declarations from different JSONDEFS and YAMLDEFS
     * resources cannot intercept local {@code #/$defs} references.
     */
    @Test
    public void AIcMutuallyRecursivePointersAreQualifiedBySourceDocument() {
        var first = declared("a.json#/$defs/Node", "Node", "a.json", "#/$defs/Node",
                reference("#/$defs/Branch", "a.json", "#/$defs/Node/properties/branch"));
        var second = declared("a.json#/$defs/Branch", "Branch", "a.json", "#/$defs/Branch",
                reference("#/$defs/Node", "a.json", "#/$defs/Branch/properties/node"));
        var foreign = declared("b.json#/$defs/Branch", "Branch", "b.json", "#/$defs/Branch",
                new AIcDefsCanonicalScalar(AIngScalarKind_1.STRING, ""));
        var linked = AIcDefsCodegenCanonicalModelLinker.link(List.of(first, second, foreign));
        Assert.assertEquals(((AIcDefsCanonicalType) linked.get(0).structure()).targetIdentity(),
                "a.json#/$defs/Branch");
        Assert.assertEquals(((AIcDefsCanonicalType) linked.get(1).structure()).targetIdentity(),
                "a.json#/$defs/Node");
    }

    /**
     * Proves that normalized flattening occurs only after the unnormalized generated
     * contract has reached the schema-validation callback.
     */
    @Test
    public void AIcSchemaValidationPrecedesNormalization() {
        var nested = new AIcDefsCanonicalElementList(AIngComposition_1.SEQUENCE,
                List.of(new AIcDefsCanonicalElement("name",
                        new AIcDefsCanonicalScalar(AIngScalarKind_1.STRING, ""),
                        List.of(), Map.of())));
        var root = declared("Root", "Root", "root.json", "#",
                new AIcDefsCanonicalElementList(AIngComposition_1.SEQUENCE,
                        List.of(nested)));
        var wasCalled = new AtomicBoolean();
        var normalized = AIcDefsCodegenCanonicalModelLinker.link(List.of(root), payload -> {
            var rootPayload = (Map<?, ?>) ((List<?>) payload.get("types")).get(0);
            var field = (Map<?, ?>) ((Map<?, ?>) rootPayload.get("structure")).get("ElementList");
            var first = (Map<?, ?>) ((List<?>) field.get("children")).get(0);
            Assert.assertTrue(first.containsKey("ElementList"));
            wasCalled.set(true);
        });
        Assert.assertTrue(wasCalled.get());
        var flat = (AIcDefsCanonicalElementList) normalized.get(0).structure();
        Assert.assertEquals(flat.children().size(), 1);
        Assert.assertTrue(flat.children().get(0) instanceof AIcDefsCanonicalElement);
    }

    /**
     * Ensures the exact offending source pointer accompanies unresolved-reference
     * diagnostics rather than falling back to an opaque ANY property.
     */
    @Test
    public void AIcMissingReferenceFailsWithSourceLocation() {
        var root = declared("missing.json#/$defs/A", "A", "missing.json", "#/$defs/A",
                reference("#/$defs/Missing", "missing.json", "#/$defs/A/properties/ref"));
        try {
            AIcDefsCodegenCanonicalModelLinker.link(List.of(root));
            Assert.fail("The missing declaration must be rejected");
        } catch (IllegalArgumentException expected) {
            Assert.assertTrue(expected.getMessage().contains("missing.json#/$defs/A/properties/ref"));
            Assert.assertTrue(expected.getMessage().contains("unresolved TYPE reference"));
        }
    }

    /**
     * Rejects invalid type inheritance cycles without rejecting ordinary recursive
     * member properties, which have already been checked separately.
     */
    @Test
    public void AIcCyclicInheritanceIsRejected() {
        var scalar = new AIcDefsCanonicalScalar(AIngScalarKind_1.ANY, "");
        var a = new AIcDefsCanonicalType("A", "A", AIngTypeOrigin_1.DECLARED,
                List.of("A"), List.of("B"), scalar, AIngResolutionState_1.RESOLVED, Map.of());
        var b = new AIcDefsCanonicalType("B", "B", AIngTypeOrigin_1.DECLARED,
                List.of("B"), List.of("A"), scalar, AIngResolutionState_1.RESOLVED, Map.of());
        try {
            AIcDefsCodegenCanonicalModelLinker.link(List.of(a, b));
            Assert.fail("Cyclic inheritance must be rejected");
        } catch (IllegalArgumentException expected) {
            Assert.assertTrue(expected.getMessage().contains("Cyclic TYPE inheritance"));
        }
    }
}
