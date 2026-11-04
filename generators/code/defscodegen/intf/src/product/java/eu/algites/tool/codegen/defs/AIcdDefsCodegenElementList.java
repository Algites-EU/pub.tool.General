package eu.algites.tool.codegen.defs;

import java.util.List;
import java.util.Objects;

/**
 * Compositional list of direct ELEMENT, ELEMENTLIST, LIST, or MAP children.
 * Unlike the legacy model, neither a native aggregator nor a wrapper element is needed.
 *
 * @param composition sequence, all, or choice semantics
 * @param children direct ordered child structures
 * @param minOccurs minimum group occurrences
 * @param maxOccurs maximum group occurrences; minus one means unbounded
 */
public record AIcdDefsCodegenElementList(AInDefsCodegenComposition composition,
        List<AIiDefsCodegenStructure> children, int minOccurs, int maxOccurs)
        implements AIiDefsCodegenStructure {
    /** Compatibility constructor: one compositional group. */
    public AIcdDefsCodegenElementList(AInDefsCodegenComposition composition,
            List<AIiDefsCodegenStructure> children) {
        this(composition, children, 1, 1);
    }
    /** Freezes the ordered children and rejects unsupported nested child kinds. */
    public AIcdDefsCodegenElementList {
        Objects.requireNonNull(composition, "composition");
        AIcDefsCodegenOccurrences.check(minOccurs, maxOccurs);
        children = List.copyOf(Objects.requireNonNull(children, "children"));
        for (var child : children) {
            Objects.requireNonNull(child, "child");
            if (child.kind() != AInDefsCodegenStructureKind.ELEMENT &&
                child.kind() != AInDefsCodegenStructureKind.ELEMENTLIST &&
                child.kind() != AInDefsCodegenStructureKind.LIST &&
                child.kind() != AInDefsCodegenStructureKind.MAP) {
                throw new IllegalArgumentException("ELEMENTLIST cannot directly contain " + child.kind());
            }
        }
    }
    /** {@inheritDoc} */
    @Override public AInDefsCodegenStructureKind kind() { return AInDefsCodegenStructureKind.ELEMENTLIST; }
}

