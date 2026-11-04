package eu.algites.tool.codegen.defs;

/** Semantic distinction between standalone maps and additional properties integrated into an object. */
public enum AInDefsCodegenMapKind {
    /** A map represented as a standalone map property. */
    COMMON_MAP,
    /** Additional properties serialized beside declared object fields without an enclosing wrapper. */
    INTEGRATED_PROPERTY_MAP
}

