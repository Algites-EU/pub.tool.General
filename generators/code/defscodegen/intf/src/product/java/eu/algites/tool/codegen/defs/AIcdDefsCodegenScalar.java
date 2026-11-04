package eu.algites.tool.codegen.defs;

import java.util.Objects;

/**
 * Primitive leaf type, retaining source format hints without choosing Java/Python types.
 *
 * @param scalarKind canonical scalar family
 * @param format original optional semantic format, or empty if absent
 */
public record AIcdDefsCodegenScalar(AInDefsCodegenScalarKind scalarKind, String format)
        implements AIiDefsCodegenStructure {
    /** Preserves the kind and normalizes an absent optional format to empty. */
    public AIcdDefsCodegenScalar {
        Objects.requireNonNull(scalarKind, "scalarKind");
        format = format == null ? "" : format;
    }
    /** {@inheritDoc} */
    @Override public AInDefsCodegenStructureKind kind() { return AInDefsCodegenStructureKind.SCALAR; }
}

