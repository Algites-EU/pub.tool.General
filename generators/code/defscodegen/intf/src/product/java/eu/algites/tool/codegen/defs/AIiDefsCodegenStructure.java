package eu.algites.tool.codegen.defs;

import java.util.Objects;

/**
 * Root of the source-independent, immutable canonical structure hierarchy.
 * Only the seven declared kinds are valid; unresolved references belong to
 * {@link AInDefsCodegenResolutionState} on a type, not this kind hierarchy.
 * Implementations are final records in the same Java module and package.
 */
public sealed interface AIiDefsCodegenStructure permits AIcdDefsCodegenType,
        AIcdDefsCodegenElementList, AIcdDefsCodegenElement, AIcdDefsCodegenList,
        AIcdDefsCodegenMap, AIcdDefsCodegenScalar, AIcdDefsCodegenEnum {
    /**
     * Gets the precise kind of this node, independent of the source schema syntax.
     *
     * @return one of the seven canonical kinds, never a temporary reference state
     */
    AInDefsCodegenStructureKind kind();

    /**
     * Checks the presence of a required child structure with a useful error path.
     *
     * @param node nested structure to validate
     * @param location field or child location used in validation messages
     * @return the non-null nested structure
     * @throws NullPointerException if node or location is null
     */
    static AIiDefsCodegenStructure requireChild(AIiDefsCodegenStructure node, String location) {
        return Objects.requireNonNull(node, Objects.requireNonNull(location, "location"));
    }
}

