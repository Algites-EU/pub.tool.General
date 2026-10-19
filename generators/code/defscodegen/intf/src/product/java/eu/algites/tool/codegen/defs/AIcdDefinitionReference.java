package eu.algites.tool.codegen.defs;

/**
 * Source-independent identity of a referenced definition and an optional recursive target shape.
 * The target type may be unknown during parsing, or may initially contain only its known root kind;
 * later reference resolution may supply the complete recursive node without introducing a flat kind field.
 *
 * @param identity canonical target identity or unresolved source URI
 * @param version expected target version, or null if unknown
 * @param logicalName naming identity of the referenced declaration
 * @param targetDataType resolved or partially known recursive type of the target, or null if unknown
 */
public record AIcdDefinitionReference(String identity, Integer version, String logicalName,
        AIcdDataType targetDataType) {
    /**
     * Indicates that a resolved target type is enumerated; unknown targets are not treated as enums.
     * This is a derived semantic query, never a second stored type descriptor.
     *
     * @return true exactly when the target's known root kind is ENUM
     */
    public boolean targetsEnum() {
        return targetDataType != null && targetDataType.kind() == AInDataTypeKind.ENUM;
    }
}
