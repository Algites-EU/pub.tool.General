package eu.algites.tool.codegen.defs;

/** The seven canonical structural kinds. Reference and undefined states are represented by resolution status, never additional structural kinds. */
public enum AInDefsCodegenStructureKind {
    /** A named or synthetic contract type. */
    TYPE,
    /** An ordered compositional group. */
    ELEMENTLIST,
    /** A named field with a nested structure. */
    ELEMENT,
    /** A homogeneous nested item collection. */
    LIST,
    /** A keyed nested value collection. */
    MAP,
    /** A primitive value. */
    SCALAR,
    /** An enumeration with a scalar base type. */
    ENUM
}

