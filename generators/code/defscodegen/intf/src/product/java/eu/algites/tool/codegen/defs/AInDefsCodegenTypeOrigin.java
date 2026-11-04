package eu.algites.tool.codegen.defs;

/** Distinguishes declared types from types introduced by a frontend for a necessary generated contract. */
public enum AInDefsCodegenTypeOrigin {
    /** Directly named in a source schema. */
    DECLARED,
    /** Constructed for an inline structure requiring an independently generated interface. */
    SYNTHETIC
}

